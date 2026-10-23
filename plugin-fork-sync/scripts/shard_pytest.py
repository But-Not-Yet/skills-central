#!/usr/bin/env python3
"""Split a pytest collect list into file-level, case-count-balanced shards.

Usage:
    python -m pytest tests/ -q --collect-only -q > collect_list.txt   # one test id per line
    shard_pytest.py collect_list.txt --shards 4 --outdir shards/

Each shard gets whole files (never split a file across shards) written to
`part<i>.txt` as a space-separated pytest-args list. Run each shard in its own
process so resources reset between shards:

    for i in 1 2 3 4; do
      pytest $(cat shards/part$i.txt) -q --tb=no -rf > shards/log$i.txt 2>&1
      echo "PART$i EXIT=$?" >> shards/log$i.txt
    done
"""
import argparse
import os
from collections import OrderedDict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collect_list")
    ap.add_argument("--shards", type=int, default=4)
    ap.add_argument("--outdir", default="shards")
    args = ap.parse_args()

    files = OrderedDict()
    for line in open(args.collect_list):
        f = line.split("::")[0].strip()
        if f.endswith(".py"):
            files[f] = files.get(f, 0) + 1
    if not files:
        raise SystemExit("no .py entries found — is the collect list valid?")

    chunks = [[] for _ in range(args.shards)]
    sums = [0] * args.shards
    # biggest-file-first keeps shards even
    for f, n in sorted(files.items(), key=lambda kv: -kv[1]):
        i = min(range(args.shards), key=lambda k: sums[k])
        chunks[i].append(f)
        sums[i] += n

    os.makedirs(args.outdir, exist_ok=True)
    for i, ch in enumerate(chunks, 1):
        path = f"{args.outdir}/part{i}.txt"
        open(path, "w").write(" ".join(ch) + "\n")
        print(f"part{i}: {len(ch)} files, {sums[i-1]} cases -> {path}")
    print(f"total: {sum(sums)} cases across {len(files)} files")


if __name__ == "__main__":
    main()
