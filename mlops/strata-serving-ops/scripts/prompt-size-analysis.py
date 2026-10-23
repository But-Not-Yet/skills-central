#!/usr/bin/env python3
"""Strata 引擎日志的提示词尺寸/复用/压缩事件统计。

用法: python3 prompt-size-analysis.py [日志路径] [--era]
默认日志: ~/Documents/LLM/Strata/strata-iq3_s.log
--era 按 engine started 分段打印每段 max/p50/zero-reuse（查外部阈值线掐顶用）。
输出: 请求数、prompt 分位数、16Ki 分桶直方图、超各候选阈值计数、
压缩签名事件（落差>50K）的重读中位代价、冷预填充速率。
日志含二进制垃圾字节，一律 rb + replace 解码；正则按日志字面量拼。
"""
import re, sys, statistics, collections
from pathlib import Path

LOG = Path.home() / 'Documents/LLM/Strata/strata-iq3_s.log'
pat = re.compile(r'prompt (\d+) tokens = (\d+) reused \+ (\d+) read in (\d+) ms')
gen = re.compile(r'(\d+) generated')

args = [a for a in sys.argv[1:]]
show_era = '--era' in args
args = [a for a in args if a != '--era']
log = Path(args[0]) if args else LOG

rows = []   # (era_line, prompt, reused, read, ms, generated_max)
cur = 0
with open(log, 'rb') as f:
    for i, raw in enumerate(f, 1):
        line = raw.decode('utf-8', 'replace')
        if 'engine started' in line:
            cur = i
        m = pat.search(line)
        if m:
            g = gen.search(line)
            rows.append((cur, int(m.group(1)), int(m.group(2)),
                         int(m.group(3)), int(m.group(4)),
                         int(g.group(1)) if g else 0))
if not rows:
    sys.exit(f'0 条 prompt 行 —— 检查日志路径/正则是否对上字面量: {log}')

ps = sorted(r[1] for r in rows)
n = len(ps)
print(f'requests: {n}')
for q in (0.5, 0.75, 0.9, 0.95, 0.99):
    print(f'p{int(q*100)}: {ps[min(n-1, int(q*n))]:,}')
print(f'max: {ps[-1]:,}')
buckets = collections.Counter((p // 16384) * 16 for p in ps)
for b in sorted(buckets):
    print(f'  {b:>4}K: {buckets[b]}')
for t in (157286, 196608, 209715, 222822):
    print(f'> {t:,} ({t/262144:.2f}x256K): {sum(1 for p in ps if p > t)}')

# 单轮最大增量与最大生成 —— 提阈值时头顶余量的实测依据
print('max single-turn read:', f'{max(r[3] for r in rows):,}',
      '| max generated:', max(r[5] for r in rows))

# 压缩签名: 相邻请求落差>50K 且后条仍>20K
drops = [(rows[i], rows[i+1]) for i in range(len(rows)-1)
         if rows[i][1] - rows[i+1][1] > 50000 and rows[i+1][1] > 20000]
if drops:
    rd = statistics.median(b[3] for _, b in drops)
    ms = statistics.median(b[4] for _, b in drops)
    ru = statistics.median(b[2] for _, b in drops)
    print(f'compression-signature events: {len(drops)} | '
          f'median after-event reused {ru:,.0f}, re-prefill {rd:,.0f} tok / {ms/1000:.1f}s')

# 冷全量预填充速率（大 read 的 tok/s 中位）
big = [(r[3], r[4]) for r in rows if r[3] > 5000 and r[4] > 0]
if big:
    rate = sorted(t / ms * 1000 for t, ms in big)
    print(f'prefill tok/s median (reads>5k): {rate[len(rate)//2]:,.0f}')

if show_era:
    eras = collections.defaultdict(list)
    for r in rows:
        eras[r[0]].append(r)
    print('--- per engine-started era ---')
    for e in sorted(eras)[-15:]:
        v = eras[e]
        ep = sorted(x[1] for x in v)
        zr = sum(1 for x in v if x[2] == 0)
        print(f'era@{e}: n={len(v)} max={ep[-1]:,} p50={ep[len(ep)//2]:,} '
              f'zero-reuse={zr} ({zr/len(v):.0%})')
