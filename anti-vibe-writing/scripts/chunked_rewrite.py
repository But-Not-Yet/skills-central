#!/usr/bin/env python3
"""切片改写管道：把大 markdown 文档按空行/标题切成 ~650 字块，逐块调外部模型重写并独立落盘，
最后 shell 拼接成完整交付（不过模型重打，防复述吸引子）。幂等：块输出文件存在即跳过，可断点续跑。
复用方法：改开头 SRC / OUTD / MERGED / SP 四个常量与任务书 ENDPOINT 即可。
任务书三守卫（见 SKILL.md 切片改写交付环）：行数守卫、数字字面守卫、temp1.0+关思考。"""
import json, os, re, time, urllib.request, pathlib

SRC = pathlib.Path("/home/alonzo/.hermes/SOUL.md")
OUTD = pathlib.Path.home() / ".hermes/kanban/workspaces/t_5fb5969b/sections"
MERGED = pathlib.Path.home() / "Documents/Hermes/AI味语义排查_20261014/apex_worker_kanban_rewrite.md"
SP = "http://10.6.0.3:8093/v1/chat/completions"

INSTR = ("把下面这段彻底重写：每一句都重新措辞、换词、调语序、改句式，删铺垫，节奏像真人。**每一行都是正文，整行不留白：不要空行、不要加空段、条目之间不隔行**，"
         "输出总行数不能超过输入行数。首行就是改写后的第一行正文（不要空行开头）。"
         "红线：数字、日期、人名、模型名、文件名、命令行参数、「」『』引号里的原话必须**字面原样书写**，"
         "不得换写成汉字数字或中文日期（18 岁不能写成十八岁，2026-10-04 不能写成 2026年10月4日）；"
         "markdown 列表符号与缩进保持原样。只输出重写后的正文，无任何说明。原文行数少就输出短，禁止用换行填充。\n\n原文：\n")

# 按行分块：块在空行/标题处切断，目标 ~650 字
lines = SRC.read_text(encoding="utf-8").splitlines()
chunks, cur = [], []
cur_len = 0
for ln in lines:
    if cur and (cur_len >= 650 and (ln.strip() == "" or ln.startswith("#"))):
        chunks.append("\n".join(cur)); cur, cur_len = [], 0
    cur.append(ln); cur_len += len(ln)
if cur: chunks.append("\n".join(cur))
OUTD.mkdir(parents=True, exist_ok=True)
print(f"chunks={len(chunks)}", flush=True)

def g6(s):
    s = re.sub(r"\s+", "", s); return {s[i:i+6] for i in range(len(s)-5)} or {s}

t0 = time.time()
for i, ck in enumerate(chunks):
    fp = OUTD / f"{i:02d}.md"
    if fp.exists() and fp.stat().st_size > 0:
        continue
    body = {"messages": [{"role": "user", "content": INSTR + ck}],
            "temperature": 1.0, "top_p": 0.95, "max_tokens": 3000,
            "chat_template_kwargs": {"enable_thinking": False}}
    for attempt in range(3):
        try:
            req = urllib.request.Request(SP, json.dumps(body, ensure_ascii=False).encode(),
                                         {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.load(r)
            out = (resp["choices"][0]["message"].get("content") or "").strip()
            break
        except Exception:
            if attempt == 2: raise
            time.sleep(10)
    # 行数守卫：模型加空行注水就压回（折叠连续空行为一个）
    out = re.sub(r"\n{3,}", "\n\n", out)
    if out.count("\n") > ck.count("\n") + 2:
        out = re.sub(r"\n(?!\n)\n+", "\n", out)
    fp.write_text(out, encoding="utf-8")
    cr = len(g6(ck) & g6(out)) / max(1, len(g6(out)))
    print(f"[{i+1}/{len(chunks)}] {round(time.time()-t0)}s in={len(ck)} out={len(out)} copy6={cr:.3f}", flush=True)

# 拼接：每块 strip 后用 \n\n 相接，正好还原块边界处被 strip 掉的原文空行
merged = "\n\n".join((OUTD / f"{i:02d}.md").read_text(encoding="utf-8").strip() for i in range(len(chunks)))
MERGED.write_text(merged, encoding="utf-8")
full_cr = len(g6(SRC.read_text(encoding='utf-8'))&g6(merged))/max(1,len(g6(merged)))
print(f"MERGED_DONE {len(chunks)} secs={round(time.time()-t0)} total_copy6={full_cr:.3f}", flush=True)
