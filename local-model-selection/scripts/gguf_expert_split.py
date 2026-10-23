#!/usr/bin/env python3
"""Compute the expert / non-expert byte split of a GGUF, reading ONLY the header.

Why: `--n-cpu-moe N` (llama.cpp) must be derived from the real tensor split, not
estimated. The non-expert tensors (attention, dense FFN, shared experts, norms,
embeddings) stay on the GPU and set the VRAM floor; the routed-expert tensors are
what you offload. Reading the header costs a few KB instead of the whole file.

Remote use: split-plan a Hub GGUF BEFORE downloading it — fetch the header with an
HTTP Range request (`Range: bytes=0-33554431`, ~32 MiB) and parse that buffer.
Do NOT shrink the range: the metadata block carries the tokenizer vocab/merges
arrays, which run past 8 MiB, and a truncated buffer dies mid-array with a struct
error. The last tensor's size is derived from the FILE size, so also supply the
real total (Content-Range, or the Hub tree API's size) or totals come out low.

Usage:
    python3 gguf_expert_split.py /path/to/model.gguf

Output: file size, expert total, non-expert total, per-layer expert average and
block count. Feed those into references/moe-offload-deployment.md to pick N.

Implementation note: tensor byte sizes are derived from consecutive `offset`
fields after sorting, NOT from a ggml type-size table. That keeps this script
independent of the type table (which changes as new quant types land).
"""
import collections
import os
import re
import struct
import sys


def read_str(f):
    n, = struct.unpack("<Q", f.read(8))
    return f.read(n).decode("utf-8", "replace")


def skip_value(f, t):
    # GGUF metadata value types
    if t in (0, 1, 7):
        f.read(1)
    elif t in (2, 3):
        f.read(2)
    elif t in (4, 5, 6):
        f.read(4)
    elif t == 8:
        read_str(f)
    elif t == 9:
        elem_t, = struct.unpack("<I", f.read(4))
        n, = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            skip_value(f, elem_t)
    elif t in (10, 11, 12):
        f.read(8)
    else:
        raise ValueError("unknown metadata value type %d" % t)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: gguf_expert_split.py <model.gguf>")
    path = sys.argv[1]

    with open(path, "rb") as f:
        if f.read(4) != b"GGUF":
            sys.exit("not a GGUF file")
        ver, = struct.unpack("<I", f.read(4))
        n_tensors, = struct.unpack("<Q", f.read(8))
        n_kv, = struct.unpack("<Q", f.read(8))

        for _ in range(n_kv):
            read_str(f)
            t, = struct.unpack("<I", f.read(4))
            skip_value(f, t)

        infos = []
        for _ in range(n_tensors):
            name = read_str(f)
            nd, = struct.unpack("<I", f.read(4))
            struct.unpack("<%dQ" % nd, f.read(8 * nd))  # dims, unused
            ttype, = struct.unpack("<I", f.read(4))
            off, = struct.unpack("<Q", f.read(8))
            infos.append((off, name))

        data_start = (f.tell() + 31) & ~31

    fsize = os.path.getsize(path)
    infos.sort()

    expert = non_expert = 0
    per_layer = collections.defaultdict(int)
    for i, (off, name) in enumerate(infos):
        if i + 1 < len(infos):
            size = infos[i + 1][0] - off
        else:
            size = fsize - (data_start + off)
        # routed experts; shared experts are always-active and stay on GPU
        is_expert = ("_exps" in name) or ("experts" in name and "shared" not in name)
        if is_expert:
            expert += size
            m = re.search(r"blk\.(\d+)\.", name)
            if m:
                per_layer[int(m.group(1))] += size
        else:
            non_expert += size

    G = 1024.0 ** 3
    print("file            = %.2f GiB" % (fsize / G))
    print("expert tensors  = %.2f GiB" % (expert / G))
    print("non-expert      = %.2f GiB   <- VRAM floor (always active)" % (non_expert / G))
    if per_layer:
        blocks = sorted(per_layer)
        avg = sum(per_layer.values()) / len(per_layer) / G
        print("expert blocks   = %d  (blk.%d..blk.%d)" % (len(blocks), blocks[0], blocks[-1]))
        print("avg per block   = %.3f GiB" % avg)
        print("-> blocks you can keep on GPU = "
              "(usable_VRAM - non_expert - KV - buffers) / %.3f" % avg)


if __name__ == "__main__":
    main()
