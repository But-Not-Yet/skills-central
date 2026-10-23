#!/usr/bin/env python3
"""Compare same-named tensors between two HuggingFace repos by HTTP Range.

Answers "is repo B just repo A with a light finetune?" without downloading
full weights. Aligns by layer index, reports per-layer cosine similarity and
relative L2 difference, plus a summary.

Usage:
    python3 hf_tensor_compare.py <repoA> <repoB> <name_substring> [--max-layers N]

Example:
    python3 hf_tensor_compare.py Qwen/Qwen3.5-35B-A3B Qwen/Qwen3.6-35B-A3B linear_attn.conv1d.weight

Reading: cosine ~0.999x with single-digit-percent relative L2 = light finetune,
not a new generation. Tensors that barely moved (relL2 ~0.000x) are the shared-
base fingerprint. Per-layer ordering shows where the change concentrated.
"""
import json
import re
import struct
import sys
import urllib.request

import numpy as np


def rget(url, start, end):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def decode(raw, dtype):
    if dtype in ("BF16", "bfloat16"):
        u = np.frombuffer(raw, dtype=np.uint16)
        return (u.astype(np.uint32) << 16).view(np.float32)
    if dtype in ("F32", "float32"):
        return np.frombuffer(raw, dtype=np.float32)
    if dtype in ("F16", "float16"):
        return np.frombuffer(raw, dtype=np.float16).astype(np.float32)
    return None


def collect(repo, substr, max_layers):
    base = f"https://huggingface.co/{repo}/resolve/main/"
    with urllib.request.urlopen(base + "model.safetensors.index.json", timeout=30) as r:
        wm = json.loads(r.read())["weight_map"]
    targets = {k: v for k, v in wm.items() if substr in k}
    shards = {}
    for k, v in targets.items():
        shards.setdefault(v, []).append(k)
    pat = re.compile(r"(?:^|\.)(\d+)\.")
    out = {}
    for shard, keys in shards.items():
        first = rget(base + shard, 0, 7)
        hlen = struct.unpack("<Q", first)[0]
        header = json.loads(rget(base + shard, 8, 8 + hlen - 1))
        data_start = 8 + hlen
        for k in keys:
            meta = header[k]
            f = decode(
                rget(base + shard, data_start + meta["data_offsets"][0],
                     data_start + meta["data_offsets"][1] - 1),
                meta["dtype"],
            )
            if f is None:
                continue
            m = pat.search(k)
            layer = int(m.group(1)) if m else -1
            out[layer] = f
    if max_layers:
        out = dict(sorted(out.items())[:max_layers])
    return out


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    repo_a, repo_b, substr = argv[1], argv[2], argv[3]
    max_layers = None
    if "--max-layers" in argv:
        max_layers = int(argv[argv.index("--max-layers") + 1])
    a = collect(repo_a, substr, max_layers)
    b = collect(repo_b, substr, max_layers)
    print(f"{substr}: A={len(a)} tensors, B={len(b)} tensors")
    print(f"{'layer':>6} {'cos_sim':>10} {'rel_L2diff':>12}")
    cosines, rels = [], []
    for layer in sorted(set(a) & set(b)):
        x, y = a[layer], b[layer]
        if x.shape != y.shape:
            print(f"{layer:>6}  shape mismatch {x.shape} vs {y.shape}")
            continue
        c = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12))
        r = float(np.linalg.norm(x - y) / (np.linalg.norm(y) + 1e-12))
        cosines.append(c)
        rels.append(r)
        print(f"{layer:>6} {c:>10.5f} {r:>12.4f}")
    if cosines:
        print(f"\nmean cos_sim={np.mean(cosines):.5f}  mean rel_L2diff={np.mean(rels):.4f}")
        print(f"min cos={np.min(cosines):.5f}  max cos={np.max(cosines):.5f}")
        print("\nTensors with relL2 < 0.01 are the shared-base fingerprint.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
