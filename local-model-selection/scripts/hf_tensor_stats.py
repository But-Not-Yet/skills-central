#!/usr/bin/env python3
"""远程读 HuggingFace safetensors 张量统计，不下载整包。

用法:
  # 单模型：逐层标准差与相对中位数倍数
  python hf_tensor_stats.py std Qwen/Qwen3.5-35B-A3B linear_attn.conv1d.weight

  # 两模型：逐层余弦相似度与相对 L2 差（核验「是否同一批权重微调」）
  python hf_tensor_stats.py cos Qwen/Qwen3.5-35B-A3B Qwen/Qwen3.6-35B-A3B linear_attn.conv1d.weight

可选第 5 个参数是层号正则，默认 layers\.(\d+)\.
只依赖标准库 + numpy。需要能直连 huggingface.co。
"""
import sys, json, struct, re, urllib.request
import numpy as np


def _get(url, start=None, end=None, timeout=90):
    hdr = {"Range": f"bytes={start}-{end}"} if start is not None else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=timeout) as r:
        return r.read()


def _decode(raw, dtype):
    if dtype in ("BF16", "bfloat16"):
        u = np.frombuffer(raw, dtype=np.uint16)
        return (u.astype(np.uint32) << 16).view(np.float32)
    if dtype in ("F32", "float32"):
        return np.frombuffer(raw, dtype=np.float32)
    if dtype in ("F16", "float16"):
        return np.frombuffer(raw, dtype=np.float16).astype(np.float32)
    raise ValueError(f"unsupported dtype {dtype!r} (1-D norms/biases are often F32)")


def _headers(repo, shard):
    base = f"https://huggingface.co/{repo}/resolve/main/{shard}"
    L = struct.unpack("<Q", _get(base, 0, 7))[0]
    return base, json.loads(_get(base, 8, 8 + L - 1)), 8 + L


def tensors(repo, suffix, layer_re=None):
    """{layer:int -> np.ndarray}，按后缀收集张量，只取需要的字节区间。"""
    idx = json.loads(_get(f"https://huggingface.co/{repo}/resolve/main/model.safetensors.index.json"))
    want = {k: v for k, v in idx["weight_map"].items() if k.endswith(suffix)}
    if not want:
        raise SystemExit(f"no tensor ending with {suffix!r} — list the shard's names to find the real suffix")
    pat = re.compile(layer_re or r"layers\.(\d+)\.")
    by_shard = {}
    for k, v in want.items():
        by_shard.setdefault(v, []).append(k)
    out = {}
    for shard, keys in by_shard.items():
        base, h, ds = _headers(repo, shard)
        for k in keys:
            meta = h[k]
            o0, o1 = meta["data_offsets"]
            m = pat.search(k)
            out[int(m.group(1)) if m else -1] = _decode(_get(base, ds + o0, ds + o1 - 1), meta["dtype"])
    return out


def cmd_std(repo, suffix, layer_re=None):
    rows = sorted((l, float(a.std()), float(np.abs(a).mean())) for l, a in tensors(repo, suffix, layer_re).items())
    med = float(np.median([r[1] for r in rows]))
    print(f"{repo} :: {suffix}   n={len(rows)}   median_std={med:.5f}")
    for l, s, am in rows:
        print(f"  L{l:>3}  std={s:.5f}  x{s / med:.3f}  absmean={am:.5f}")


def cmd_cos(repo_a, repo_b, suffix, layer_re=None):
    a, b = tensors(repo_a, suffix, layer_re), tensors(repo_b, suffix, layer_re)
    cs, rs = [], []
    for l in sorted(set(a) & set(b)):
        x, y = a[l], b[l]
        if x.shape != y.shape:
            continue
        c = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12))
        r = float(np.linalg.norm(x - y) / (np.linalg.norm(y) + 1e-12))
        cs.append(c)
        rs.append(r)
        print(f"  L{l:>3}  cos={c:.5f}  relL2={r:.4f}")
    if cs:
        print(f"mean cos={np.mean(cs):.5f}   mean relL2={np.mean(rs):.4f}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    mode, lr = sys.argv[1], (sys.argv[5] if len(sys.argv) > 5 else None)
    if mode == "std":
        cmd_std(sys.argv[2], sys.argv[3], lr)
    elif mode == "cos":
        cmd_cos(sys.argv[2], sys.argv[3], sys.argv[4], lr)
    else:
        print(__doc__)
