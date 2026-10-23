#!/usr/bin/env python3
"""远程统计 HuggingFace safetensors 里匹配某模式的张量 std/absmean，按层排序。

用法:
    python hf_tensor_stats.py <repo> <name_substring>      # 统计匹配张量
    python hf_tensor_stats.py <repo> --list                # dump 张量名谱系（层号折叠为 .N.）

例:
    python hf_tensor_stats.py Qwen/Qwen3.5-35B-A3B --list
    python hf_tensor_stats.py Qwen/Qwen3.5-35B-A3B conv1d

只用 HTTP Range 取目标张量字节，不下载完整权重。需要 numpy。
判据：先看 median std，再看每层 x/med；尖峰层要做同层与跨模型对照。
"""
import sys
import json
import struct
import re
import urllib.request

import numpy as np


def rget(url, start, end):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def decode(raw, dtype):
    dt = dtype.upper()
    if dt in ("BF16", "BFLOAT16"):
        u = np.frombuffer(raw, dtype=np.uint16)
        return (u.astype(np.uint32) << 16).view(np.float32)
    if dt in ("F32", "FLOAT32"):
        return np.frombuffer(raw, dtype=np.float32)
    if dt in ("F16", "FLOAT16"):
        return np.frombuffer(raw, dtype=np.float16).astype(np.float32)
    return None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    repo, pat = sys.argv[1], sys.argv[2]
    base = f"https://huggingface.co/{repo}/resolve/main/"
    idx = json.loads(
        urllib.request.urlopen(base + "model.safetensors.index.json", timeout=30).read()
    )
    wm = idx["weight_map"]

    if pat == "--list":
        for k in sorted({re.sub(r"\.\d+\.", ".N.", k) for k in wm}):
            print(k)
        return

    tgts = {k: v for k, v in wm.items() if pat in k}
    if not tgts:
        print(f"no tensor contains {pat!r}; rerun with --list to dump name patterns")
        return

    by_shard = {}
    for k, v in tgts.items():
        by_shard.setdefault(v, []).append(k)

    rows = []
    for sh, ks in by_shard.items():
        first = rget(base + sh, 0, 7)
        hdr_len = struct.unpack("<Q", first)[0]
        h = json.loads(rget(base + sh, 8, 8 + hdr_len - 1))
        data_start = 8 + hdr_len
        for k in ks:
            v = h[k]
            o0, o1 = v["data_offsets"]
            f = decode(rget(base + sh, data_start + o0, data_start + o1 - 1), v["dtype"])
            if f is None:
                print(f"skip {k}: unsupported dtype {v['dtype']}")
                continue
            m = re.search(r"\.(\d+)\.", k)
            rows.append(
                (int(m.group(1)) if m else -1, float(f.std()), float(np.abs(f).mean()),
                 v["dtype"], tuple(v["shape"]))
            )

    rows.sort()
    stds = np.array([r[1] for r in rows])
    med = float(np.median(stds))
    print(f"{repo}  tensors={len(rows)}  dtype={rows[0][3]}  shape={rows[0][4]}")
    print(f"median std={med:.5f}")
    print(f"{'layer':>6}{'std':>12}{'x/med':>8}{'absmean':>12}")
    for lay, s, am, _, _ in rows:
        print(f"{lay:>6}{s:>12.5f}{s / med:>8.3f}{am:>12.5f}")


if __name__ == "__main__":
    main()
