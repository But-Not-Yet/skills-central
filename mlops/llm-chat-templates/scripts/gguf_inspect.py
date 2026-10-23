#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect GGUF metadata without loading the model.

Reads only the header + KV block (seeks past tensor data), so it is fast even on
multi-GB files. ASCII-only stdout on purpose -- Windows consoles are GBK and will
mangle non-ASCII, which makes parser output unreadable through ssh.

Usage:
    python gguf_inspect.py model.gguf
    python gguf_inspect.py a.gguf b.gguf --outdir /tmp/tpl
    python gguf_inspect.py a.gguf --vocab-check '<|im_start|>' '<|im_end|>' '<|endoftext|>'

What it prints per file:
  - size, block count, KV-head count, head dim, context length, MoE expert counts
  - sha256 + char count of the embedded chat template, dumped to <name>.template.jinja
  - with --vocab-check: whether each given string is a single token in the vocab

The hash is the point: compare it against a running server's live template to prove
which template is actually being used:

    curl -s localhost:8080/props | jq -r .chat_template | sha256sum

Note: the template file is written next to its OUTPUT name (see --outdir), NOT next to
the GGUF unless you ask for it -- pass --outdir . to drop them in the cwd.
"""
import argparse
import hashlib
import json
import os
import struct
import sys


def _rd(f, fmt):
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))[0]


def _rdstr(f):
    n = _rd(f, "<Q")
    return f.read(n).decode("utf-8", "replace")


_TYPES = {
    0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i",
    6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d",
}


def _rdval(f, t):
    if t == 8:
        return _rdstr(f)
    if t == 9:
        et = _rd(f, "<I")
        n = _rd(f, "<Q")
        return [_rdval(f, et) for _ in range(n)]
    return _rd(f, _TYPES[t])


# Keys worth keeping even if the caller did not ask, grouped by what they answer.
_INTERESTING = (
    "block_count", "head_count", "head_dim", "key_length", "value_length",
    "context_length", "expert_count", "expert_used", "embedding_length",
    "full_attention_interval", "rope", "layer_types",
)


def read_meta(path, want_vocab=False):
    meta = {}
    with open(path, "rb") as f:
        if f.read(4) != b"GGUF":
            raise ValueError("not a GGUF file")
        meta["__version"] = _rd(f, "<I")
        meta["__tensors"] = _rd(f, "<Q")
        n_kv = _rd(f, "<Q")
        for _ in range(n_kv):
            key = _rdstr(f)
            vtype = _rd(f, "<I")
            if key == "tokenizer.ggml.tokens":
                meta[key] = _rdval(f, vtype) if want_vocab else None
                if not want_vocab:
                    continue
            elif key == "tokenizer.chat_template" or any(
                s in key for s in _INTERESTING
            ):
                meta[key] = _rdval(f, vtype)
            else:
                _rdval(f, vtype)
    return meta


def fmt_params(m):
    rows = []
    for k in sorted(m):
        if k.startswith("__"):
            continue
        if any(s in k for s in _INTERESTING) or "head_count" in k:
            v = m[k]
            if isinstance(v, list) and len(v) > 12:
                v = "[%s ... %s] (%d)" % (v[0], v[-1], len(v))
            rows.append((k, v))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gguf", nargs="+")
    ap.add_argument("--outdir", default=None,
                    help="where to write <name>.template.jinja (default: alongside the gguf)")
    ap.add_argument("--vocab-check", nargs="*", default=None, metavar="TOKEN",
                    help="scan tokenizer.ggml.tokens for these strings")
    args = ap.parse_args()

    for path in args.gguf:
        if not os.path.exists(path):
            print("MISSING  %s" % path)
            continue
        try:
            m = read_meta(path, want_vocab=args.vocab_check is not None)
        except Exception as exc:  # noqa: BLE001
            print("ERROR    %s  %s" % (os.path.basename(path), exc))
            continue

        name = os.path.basename(path)
        size = os.path.getsize(path)
        print("=" * 78)
        print("FILE     %s  (%.2f GiB, gguf v%s)" % (name, size / 2 ** 30, m.get("__version")))

        for k, v in fmt_params(m):
            print("  %-50s %s" % (k, v))

        # KV-cache math reminder: only full-attention layers need a cache.
        kvh = None
        hd = None
        blocks = m.get("llama.block_count")
        for k, v in m.items():
            if k.endswith("attention.head_count_kv") and isinstance(v, int):
                kvh = v
            if k.endswith("attention.key_length") and isinstance(v, int):
                hd = v
        if kvh and hd and blocks:
            nl_full = blocks
            interval = m.get("llama.attention.full_attention_interval") \
                or m.get("qwen35.attention.full_attention_interval")
            if isinstance(interval, int) and interval > 1:
                nl_full = blocks // interval
                print("  %-50s %s/%s (hybrid attention)" % ("full-attention layers", nl_full, blocks))
            per_tok = kvh * hd * 2 * nl_full
            print("  %-50s %s" % ("KV values/token (q8_0 ~1.0625 B)", per_tok))
            for ctx in (65536, 131072, 196608, 262144):
                print("  %-50s %6.2f GiB" % ("  ctx %d" % ctx, per_tok * ctx * 1.0625 / 2 ** 30))

        tpl = m.get("tokenizer.chat_template")
        if tpl is None:
            print("  CHAT_TEMPLATE: absent")
        else:
            outdir = args.outdir or os.path.dirname(os.path.abspath(path))
            os.makedirs(outdir, exist_ok=True)
            out = os.path.join(outdir, os.path.splitext(name)[0] + ".template.jinja")
            with open(out, "w", encoding="utf-8") as g:
                g.write(tpl)
            digest = hashlib.sha256(tpl.encode()).hexdigest()
            print("  CHAT_TEMPLATE: %d chars  sha256=%s" % (len(tpl), digest))
            print("    written -> %s" % out)
            print("    compare: curl -s localhost:8080/props | jq -r .chat_template | sha256sum")

        if args.vocab_check:
            toks = m.get("tokenizer.ggml.tokens") or []
            vocab = set(toks)
            print("  VOCAB: %d tokens" % len(vocab))
            for w in args.vocab_check:
                print("    %-24s %s" % (w, "PRESENT" if w in vocab else "absent"))


def _json_dump(obj):
    # helper kept for callers that want machine-readable output
    return json.dumps(obj, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main())
