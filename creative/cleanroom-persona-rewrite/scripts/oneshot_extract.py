#!/usr/bin/env python3
"""从 `hermes -p <profile> chat --query-file ... --oneshot` 的原始输出中提取正文。

用法：python3 oneshot_extract.py <raw文件> <输出文件>
原始输出结构：英文推理段 + 工具日志 → 正文包在 ╮ 与 ╰ 框线之间 → 尾部会话恢复提示。
正文每行可能带 │ 前缀，逐行剥掉。退出码 2 = 没找到框（调用失败或被拒），raw 尾部已打印供排查。"""
import re
import sys

raw = open(sys.argv[1]).read()
if '\u256e' in raw and '\u2570' in raw:
    body = raw.split('\u256e', 1)[1].split('\u2570')[0]
    body = re.sub(r'^\s*[\u2502\u2503]\s?', '', body, flags=re.M)
    body = '\n'.join(l for l in body.split('\n') if not re.match(r'^\s*[\u2500\u2501]+\s*$', l)).strip()
    open(sys.argv[2], 'w').write(body + '\n')
    print(f'OK {len(body)} chars -> {sys.argv[2]}')
else:
    print(f'FAIL no box, raw {len(raw)} bytes; tail:')
    print(raw[-400:])
    sys.exit(2)
