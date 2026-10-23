#!/usr/bin/env python3
"""读 GGUF 头部，算专家 / 非专家 拆分与每层专家体积。用于 MoE 专家卸载预算。

只读文件头，不需要整模型（本机文件直接读；远端可先 Range 取前 ~32 MB 落盘再喂进来）。

    python gguf_split.py <path.gguf>

原理：tensor_info 里每个张量带 offset，按 offset 排序后**相邻差值 = 该张量字节数**，
无需解析 ggml 类型表。末位张量无后继，用「文件大小 − 末端 offset」兜底估算。

为什么需要它：**非专家权重（注意力 / 嵌入 / 共享专家 / norm）必须常驻显存，是显存预算的大头**，
只有路由专家可卸载。不把这两类分开，算出来的卸载层数一定是错的。

注意：若引擎走 `--fit on` 自动分配，本脚本输出用于**预测与复核**，不是要写进命令行的参数。
"""
import collections
import os
import re
import struct
import sys


def read_string(f):
    n, = struct.unpack("<Q", f.read(8))
    return f.read(n).decode("utf-8", "replace")


def skip_value(f, t):
    """跳过一个 GGUF metadata 值（数组递归）。"""
    if t in (0, 1, 7):
        f.read(1)
    elif t in (2, 3):
        f.read(2)
    elif t in (4, 5, 6):
        f.read(4)
    elif t == 8:
        read_string(f)
    elif t == 9:
        et, = struct.unpack("<I", f.read(4))
        n, = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            skip_value(f, et)
    elif t in (10, 11, 12):
        f.read(8)
    else:
        raise ValueError("unknown gguf value type %d" % t)


KEEP = ("block_count", "expert_count", "expert_used_count", "context_length",
        "embedding_length", "feed_forward_length", "expert_feed_forward_length",
        "attention.head_count", "attention.head_count_kv",
        "attention.key_length", "attention.value_length",
        "architecture", "rope.freq_base")


def main(path):
    f = open(path, "rb")
    f.read(4)                                        # magic
    ver, = struct.unpack("<I", f.read(4))
    n_tensors, = struct.unpack("<Q", f.read(8))
    n_kv, = struct.unpack("<Q", f.read(8))
    print("GGUF v%d  tensors=%d  kv=%d" % (ver, n_tensors, n_kv))

    meta = {}
    for _ in range(n_kv):
        key = read_string(f)
        t, = struct.unpack("<I", f.read(4))
        if key.split(".")[-1] in KEEP and t in (4, 5, 6, 8, 10):
            if t == 8:
                meta[key] = read_string(f)
            elif t == 4:
                meta[key] = struct.unpack("<I", f.read(4))[0]
            elif t == 5:
                meta[key] = struct.unpack("<i", f.read(4))[0]
            elif t == 10:
                meta[key] = struct.unpack("<Q", f.read(8))[0]
            else:
                meta[key] = round(struct.unpack("<f", f.read(4))[0], 1)
        else:
            skip_value(f, t)

    tensors = []
    for _ in range(n_tensors):
        name = read_string(f)
        n_dims, = struct.unpack("<I", f.read(4))
        f.read(8 * n_dims)                           # dims，用不上
        f.read(4)                                    # ggml type，用不上（靠 offset 差值）
        offset, = struct.unpack("<Q", f.read(8))
        tensors.append((offset, name))
    tensors.sort()

    gib = float(1024 ** 3)
    total = os.path.getsize(path)
    expert = non_expert = 0
    per_layer = collections.defaultdict(int)
    for i, (offset, name) in enumerate(tensors):
        size = (tensors[i + 1][0] - offset) if i + 1 < len(tensors) else (total - offset)
        is_expert = ("_exps" in name) or ("experts" in name and "shexp" not in name and "shared" not in name)
        if is_expert:
            expert += size
            m = re.search(r"blk\.(\d+)\.", name)
            if m:
                per_layer[int(m.group(1))] += size
        else:
            non_expert += size

    print("META:")
    for k, v in sorted(meta.items()):
        print("   %s = %s" % (k, v))
    print("SPLIT:")
    print("   experts      %7.2f GiB  (%4.1f%%)" % (expert / gib, expert / (expert + non_expert) * 100))
    print("   non-expert   %7.2f GiB   <- 必须常驻显存" % (non_expert / gib))
    print("   file total   %7.2f GiB" % (total / gib))
    if per_layer:
        avg = sum(per_layer.values()) / len(per_layer) / gib
        print("   expert layers %d (blk %d-%d), per layer %.3f GiB"
              % (len(per_layer), min(per_layer), max(per_layer), avg))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
