---
name: anti-vibe-writing
description: 'Use when the user wants to humanize, de-AI, polish, or warm up an AI-generated document, in English or Chinese. Good for social posts (X/Weibo/Jike/RedNote), Reddit and forum comments, blogs, podcast show notes, README cleanup, product docs, landing page copy, proposals, founder notes, and technical memos. Removes templated phrasing, consultant-speak, vague abstraction, emoji or icon headings, markdown templates, overly balanced tone, and the typographic tells that flag generated text (em-dashes `—`/`——`, smart quotes, the `…` character) while preserving meaning. Supports optional voice modes: human-texture (light irregularities) and learning mode (match a specific host''s style from samples).'
argument-hint: 'Paste the draft, or describe the document, audience, scenario (tweet/weibo/reddit/blog/podcast/report), how much structure should remain, and optionally provide host samples for learning mode.'
user-invocable: true
disable-model-invocation: false
metadata:
  version: 1.7.0
  language_support: [en, zh]
  tools: [Read, Edit, Write, Grep, Glob, Bash, WebFetch, WebSearch, TaskCreate, Agent]
---

# Anti-Vibe Writing

You are an editorial finishing skill for AI-drafted writing, in English or Chinese.

Use this after the substance is already there. The point is not to make the prose prettier. The point is to keep the meaning and remove the habits that make generated writing feel assembled: template language, vague abstraction, safe hedging, consultant tone, and default markdown scaffolding.

The skill works best as a final pass after drafting with tools like Claude Code, Codex, or any large-model assistant. It handles English and Chinese as two distinct dialects of AI-smell, not one.

## Core Philosophy

- Preserve the writer's meaning. Improve delivery, not substance.
- Human writing chooses what matters. AI writing often hedges, formats, and explains by habit.
- Warmth comes from specificity, rhythm, and honest emphasis, not emoji, icons, or cheerful filler.
- Chinese AI-smell and English AI-smell are different problems. Apply the matching reference.
- Several narrow editing passes work better than one vague rewrite.
- Clean is not the goal. Sounding like the person who meant it is the goal.

## Best Uses

- The draft is correct but flat, generic, or obviously AI-written.
- The document has too many headings, bullets, or numbered lists.
- The copy sounds cautious, polished, and empty at the same time.
- The writing leans on business-speak instead of saying what is true.
- The reader needs prose that sounds deliberate rather than generated.
- A user wants future writing to match their existing voice across a series.

## Typical Fits

- Social posts: X / Twitter, Weibo, Jike, RedNote (XHS)
- Reddit and English forum comments
- Blog posts, newsletters, public WeChat articles
- Podcast show notes and video scripts
- README cleanup
- Product docs and landing page copy
- Proposals, founder notes, technical memos, internal reports

See [scenario-presets.md](./references/scenario-presets.md) for per-scenario constraints.

## Do Not Use For

- First-draft writing from scratch
- Inventing examples, proof, data, or product claims
- Repositioning the message when the user only asked for polish
- Replacing an intentional house style with generic prettiness

## Before You Rewrite

1. Identify the job of the document and the scenario (use [scenario-presets.md](./references/scenario-presets.md) to pick constraints).
2. Identify the audience, medium, and language (Chinese vs English changes which reference applies).
3. Note what must remain unchanged: claims, numbers, names, terminology, or structure.
4. Decide how much markdown the piece actually needs.
5. Check whether a host profile applies (learning mode).
6. Decide which voice mode to run in (see below).
7. Ask for missing context only if it would materially change the rewrite.

## Voice Modes

The skill runs in one of three voice modes. **Default mode** is the safe baseline. The other two are opt-in.

### Mode 1: Default (Clean)

Strip AI-smell, return a clean, professional version. Conservative. Suitable for most product, documentation, and professional contexts.

This is what runs unless the user opts into something else.

### Mode 2: Human Texture (Opt-in)

Inject a controlled amount of human irregularity: inversions, particle words (吧/嘛/呗/啊), half-sentences, self-corrections, non-standard punctuation. Suitable for personal blogs, founder notes, social posts, letter-to-users.

Triggered by user signals such as:
- "Loosen it up" / "放松一点" / "blog voice" / "make it feel personal"
- "Like the founder actually wrote it"
- "A little less polished is fine"

Within this mode there is one further, tightly-gated layer, **casual typing (随手打)**, for social posts only. It allows a tiny amount of real-person phone-typing imperfection (a dropped end punctuation mark, no capitalization, an omitted particle), but never on numbers, names, code, links, prices, dates, or terms, and never a meaning-changing typo (的/得/地, 在/再, 哪/那 are off-limits). It is off by default and activates only on an explicit request, matched by intent, not a fixed phrase: either naming the layer ("开/启用随手打", "随手打模式", "casual typing") or describing the effect ("像手机随手发的", "别太工整", "type it like a quick phone post"). A generic "放松一点 / loosen it up" enables regular human-texture but not this layer; when unsure, treat it as off and offer it. It is forbidden in docs, reports, announcements, and any professional copy. When used, cap it at 1–2 touches and state them at the end. This is phone-typing texture, not error injection to evade AI detection. See the 随手打 section in [human-texture.md](./references/human-texture.md).

Details and concrete techniques: [human-texture.md](./references/human-texture.md).

### Mode 3: Learning Mode (Opt-in, sample-driven)

Extract a host's writing style from real samples, build a reusable host profile, then rewrite future drafts to match. Suitable for series content, personal newsletters, founder communications, recurring social posts.

Triggered by:
- User provides samples ("here's how I usually write on Twitter")
- User asks "can you learn my style"
- After several rewrites the user still says "this isn't like me"

Workflow: [learning-mode.md](./references/learning-mode.md). Profile template: [host-profile-template.md](./assets/host-profile-template.md). Extraction prompt: [style-extraction-prompt.md](./assets/style-extraction-prompt.md).

Modes 2 and 3 can combine with each other and with scenario presets. Order of precedence when they conflict:
1. Host profile's "禁忌词 / forbidden words" (highest)
2. Scenario preset's format constraints (length, structure, emoji policy)
3. Host profile's voice signals (sentence shape, particles, punctuation)
4. Human-texture conventions (lowest, only fills gaps)

## Output Goals

- More human rhythm
- More intentional structure
- Cleaner phrasing
- Stronger voice
- Less AI smell
- Sounds chosen by a person, not assembled by a system

## Human Passes

Use the step-by-step framework in [human-passes.md](./references/human-passes.md).

- Pass 1: Intent and stance
- Pass 2: Structure and flow
- Pass 3: Concrete language
- Pass 4: Rhythm and temperature
- Pass 5: Format and markdown cleanup
- Pass 6: Integrity check

For lighter edits, run Pass 1, Pass 3, Pass 5, then the final checklist.

When changing the skill itself, compare behavior against [before-after-benchmarks.md](./references/before-after-benchmarks.md) and [chinese-before-after.md](./references/chinese-before-after.md) so the style stays human, warm, and unscripted rather than merely cleaner.

## Default Editing Moves

- Preserve facts, claims, scope, and technical meaning.
- Detect language first. For Chinese drafts, apply [chinese-patterns-to-remove.md](./references/chinese-patterns-to-remove.md). For English, apply [patterns-to-remove.md](./references/patterns-to-remove.md).
- Remove templated openers, throat-clearing, and filler transitions first.
- Replace vague nouns and abstractions with concrete nouns and verbs.
- Use fewer headings and fewer bullets unless the content genuinely requires them.
- Collapse repetitive framing and duplicate summary language.
- Prefer an earned point of view over fake balance.
- Cut consultant-speak, hype, and process jargon. In Chinese this includes 赋能 / 打通 / 闭环 / 抓手 / 链路 and friends.
- Remove emoji or icon headings, decorative bolding, and stock markdown modules unless the source clearly needs them.
- Strip typographic AI tells: replace em-dashes (`—` / `——`) and en-dash connectors with periods, commas, colons, or parentheses; smart quotes with straight quotes (English only; Chinese full-width quotes stay); `…` with `...`. This makes the text genuinely read like keyboard typing, not as a trick to dodge detectors.
- Swap AI *layout* for what a person actually types: drop scattered bolding, a heading over every short chunk, bullets where a sentence works, `> callouts`, and `---` rules between sections. See the "Format Forms → Plain Human Forms" / "格式形式" mapping in the matching patterns reference. Test: if you wouldn't type the formatting into a message to a friend, cut it.
- Keep sentences varied in length, but not ornamental.
- Prefer prose over bullets when list structure adds no value.
- Let warmth come from concrete detail and restraint, not upbeat filler.
- Do not invent examples, numbers, or evidence.
- Default to returning rewritten copy, not commentary.

## What to Remove Early

- Typographic tells, the fastest thing readers and detectors catch: em-dashes (`—` / `——`), en-dashes used as connectors, smart quotes `“ ” ‘ ’`, the `…` character, and stray `→ • ·` in prose. Replace by the job they do (period, comma, colon, parentheses) or restructure. See the typographic sections in the matching patterns reference.
- Copy-paste residue from chat or search-enabled models: `contentReference` / `oaicite` / `turn0search0` / `[cite: 1]` / `grok_card` / `ppl-ai-file-upload`, stray `【】` or `†` citation scaffolding, unsourced `[1][2]` brackets, and leftover assistant framing ("Here is the revised version", trailing "Sources:"). Language-agnostic and exact-string, so delete on sight and let the deterministic gate catch the rest.
- Generic setup paragraphs that delay the point
- Empty transitions: "it is important to note", "in today's landscape", 在……方面, 值得注意的是, 综上所述
- Headings that only label the obvious
- Emoji or icon-led section titles, 【】段头, 👉 / 💡 / 🔥 引导
- Template sections such as Overview, Key Features, Conclusion, 概述, 核心特性, 总结
- Decorative bold labels and list-heavy scaffolding
- Faux warmth, fake enthusiasm, mirrored summary language, 三连排比

## Editing Heuristics

- If a heading only labels the obvious, cut it.
- If three bullets can become one sentence, merge them.
- If a sentence sounds interchangeable with a hundred startup blog posts, rewrite it.
- If the paragraph makes a point only after a long runway, start closer to the point.
- If the tone keeps "balancing" instead of deciding, make the claim and carry the nuance in the sentence rather than around it.
- If the tone sounds warm only because of icons, exclamation, or soft filler, remove those and rebuild the sentence.
- Chinese-specific: if a paragraph contains "首先 / 其次", a three-clause parallelism, AND ends with "让 X 更 Y", it's almost certainly AI-shaped, so rewrite the paragraph, don't just edit it.
- Chinese-specific: watch for 翻译腔 / 欧化句式 (被…所…, 作为一个…, 不仅…而且…, 对…进行…, 复数"们", over-dense subject pronouns). These read like machine translation even when no buzzword is present. Restore active voice and verbs.
- Chinese-specific: drop the "资深文案 / 营销专家" stance; it pulls in ad vocabulary. Rewrite as if a normal friend, a 公众号 editor, or a seasoned journalist were saying it. Read the result aloud; if you wouldn't talk to a friend that way, edit again. See the 改写心态 section in [chinese-patterns-to-remove.md](./references/chinese-patterns-to-remove.md).

## Task Questions

- What language is the draft in? (Different rules apply.)
- What scenario is this for? (Tweet / Weibo / Reddit / blog / podcast / report, picks the preset.)
- Who is reading this?
- What should the reader understand, feel, or do after reading it?
- Which claims, names, or terms cannot change?
- Should the markdown be preserved, reduced, or rebuilt?
- Which voice mode? Default, human texture, or learning mode?
- If learning mode: are samples available?

## Deterministic Chinese Gate (ste-lint-zh)

`python3 ~/.hermes/scripts/ste-lint-zh.py <file>` — controlled-Chinese linter (stdlib-only, from lemonhall/asd-ste100-skill-zh; exit 1 when hard violations exceed `--baseline`, default 0). Run it as the mechanical first check on any Chinese deliverable, before the human passes. Hard rules: `semicolon`, `long-sentence` (>40 chars; pass `--max-chars 25` for procedural text), `nominalization` (虚动词 进行/加以/作出+名词), `marketing-adjective`, `empty-phrase`, `synonym-rotation`. Advisory (never fail the run): `passive-voice`, `compound-aspect`, `vague-word`, `halfwidth-punct`, `dash-join`.

- **Hedges are content, never style.** 可能 / 也许 / 大概 / 有时 / 倾向于 carry the author's confidence level — shortening "请求可能已失败" to "请求失败" changes the claim, not just the wording. The linter never flags modality; neither delete nor promote a hedge during any rewrite pass.
- **Quoted banned words are records, not usage.** When a deliverable cites a banned word as an example (in quotes), register an exemption line (file, line, rule, reason) instead of deleting it; an unregistered exemption does not count.
- **Gate your own deliverable.** Any artifact that itself prescribes style rules (task books, reports, SOUL edits) must pass its own gate: zero hard violations, or per-line registered exemptions in the artifact.
- **Sweep recipe** (auditing many files, e.g. SOUL/memories/skills): run `--json` per file; classify zh vs en by CJK char count (≥150 CJK → Chinese track, else skip — the linter is Chinese-only and meaningless on English); aggregate findings by rule and by file; report per-file hard counts sorted descending so the worst files get fixed first. Keep `.bak` copies before editing so before/after counts can be re-verified on demand.
- Zero violations only means the mechanical checks passed: it does not prove meaning preservation or human voice. The human passes still follow.
- **词表/正则批扫只是第一张便宜的网，不是语义排查的替代**：构式家族（词表抓不到的重复句式，如「是X不是Y」对照模板）、高/中/低分档、上下文豁免都要逐文件语义精读。两种方法对照时用行号集合求交集报增量（重合多少、各自独有是什么、误报在哪），别宣称一种覆盖另一种。
- **大批量语义排查先跑一个文件的试点**：产物过主人目、定分档口径后再铺卡。本地小模型即可胜任精读+标注；验收方式是复核它报的行号与引文是否实锤、数字与原文是否对得上。
- **外部改写模型 jialinyyzz/humanizer (12B)：英文可用，中文不可用（2026-10-15 全篇 SOUL.md 实测判决）**。纯 completion 模型不吃 chat——prompt 按 `prompt_format.json` 字节级拼 `instr + "\n\n" + draft.strip() + sep`；采样显式全给 temp 1.0/top_p 0.95/top_k 0/min_p 0/repeat_penalty 1.0、不发 stop。实测结论：① 中文输出是碎词汤（「有猫耳无耳人」「求亲亲。不吃。等。」），68/87「干净片」也只是数字与字数干净， prose 全是翻译腔；短输入（<80 字，标题行/表格行）19/87 直接幻觉续写（26 字标题续出整出洗脸盆失窃案）。② 它 95% 过检测器、90% 事实保全的数据全部来自英文 210 篇；卡片自认中文落后（中文事实无问题仅 149/204）。③ NSFW 不回避不消毒（性奴/蹂躏/母狗原样在），但有单词级换写（媚骨 3→2）——风险是换词不是拒答。④ 采样参数与官方逐项相符仍这结果，不是参数锅。速度：笔记本 5070Ti 上 humanizer tg 39.6，低于生产机 Strata 实测加权 64.6（日志 8.8M tok 样本，MTP 投机解码开启）——它连速度都不赢。中文改写别用它；英文长文若要用，走官方 hz 工具的自动分块（跳过标题表格、~600字/块），且改完必须人读。⑤ 对照：Spark X2.5-4B abliterated 正文腔调比它像人，但思考型模型整篇任务思考吞预算（生成量 5 倍、13/87 正文截断）——小模型两头都不行。⑥ **复述吸引子 = 长输入 × 严格保真令，双因子缺一不可（隔离实验实测）**：中长篇文档（>10k token）整篇一次喂，输出塌回逐行照抄（复制率 ≥0.99），与模型规模（4B→35B）、思考开关、挂不挂 persona、指令松紧、任务书厚度全部无关——挂载含验收判据的厚任务卡照样 99% 照抄；机理是长上下文逐 token 生成时复制刚见过的串是低阻力路径，指令掰不回；MoE 算激活参数不算总参。位置效应：厚任务书下模型开头几节确实动真重写（换词调序俱全），过两三节即滑回复制——开头是注意力最富位置，撑不起全文。任务书应写进执行方式（切片、拼接不过模型重打），别指望喂给模型自己切。短片（300–800 字）配严格「事实数字逐字保留」令仍会塌到均值 0.6–0.7（近半片整片照抄）——严格保真令本身就抽走改写自由度。胜出配方（35B-A3B 实测达标）：~500 字切片 + 宽松重写令（每句重新措辞换词调语序、明令「句子结构必须换掉」、红线收窄到数字/日期/名称/引号原话）→ 19/20 片深度重写、复制率均值 0.149、语义完整无幻觉无碎词，单片中位 3.3 秒（5070Ti 上 A3B 全篇长文几分钟级）——外部模型并行改写线按此配方成立可用。块也别太短——<80 字的标题行/表格行会诱发幻觉续写。改写主力仍是本地对话模型+本技能六步 human passes+ste-lint-zh 闸（该流程的按行分组循环天然避开吸引子）；外部模型按配方做并行提速，或做只读语义排查（看板试点已证）。验收两坑：模型会把数字换成等价形式（18→十八岁、2026-10-04→2026年10月4日、编号列表→中文序号），要求字面保真必须在令中明写「数字不得改写形式」；程序化数字串对账会把这类换写全报成丢失，误报必须人眼复核后才算丢失。对照实验一律跑在被试点名的机器与模型上，本机/生产模型只当对照基线与评审，不许中途换被测对象。
- **切片改写交付环（外部模型+外部任务书，2 万字 22 块实测）**：任务书三道守卫一个不能少——①「输出总行数 ≤ 输入行数、条目间不加空行」（模型爱用空行注水，撑爆交付并坏行数验收）；②「数字/日期**字面原样书写**、不得改写成汉字形式」（不写这条，18→十八岁、2026-10-04→2026年10月4日 会全篇发生，直接坏数字保全判据）；③temp 1.0 + 关思考、max_tokens 给输入的约 4 倍。每块独立落盘 + 幂等断点续跑 + shell 拼接终稿（不过模型），全文 copy6 ~0.55、数字零丢失、全程分钟级。**切块后位置效应仍在**：变更摘要开头的块与规则密集块即便单独成片仍整片照抄（5/22，copy6>0.9）——模型肯不肯改写取决于题材与它在文中的性质，不是任务书松紧；补救只对点名块跑二遍宽松令（1–2 分钟），别全量重跑。**禁词命中先回原文分类**：grep 原文——原文逐字含该词、交付照搬 = 继承豁免（原文自引术语）；原文无、交付新生 = 模型违规，当场修且同步修改对应块文件，块文件与交付保持一致才可审计。worker 自报计数是交卷时刻的快照，主会话交卷后又改过交付物时，终审前活体重跑程序检，别拿两边快照互相印证。

## Clean-room rewriter（重写 persona/系统提示词文件时必用）

SOUL/MEMORY/USER 这类每轮注入的人格文件，本会话 agent 自己就是污染源（天天读同一批文件，改自己=回音）。手术刀换成只吃外部腔调的隔离 Hermes 人格（净空 profile + 社区来源卡当 SOUL），产物过审计交主人验收替换——完整流水线见 [cleanroom-profile-rewrite.md](./references/cleanroom-profile-rewrite.md)。

主人对这类重写的常驻口径（每条都是明文拍板过的）：
- **忠实重写不是缩写**：原文每一层意思都要在，不丢不增不删；允许结构重排。
- 引语、[事-N] 类指针、日期裁定、数字、路径、表格行列逐字保留。
- memory 条目：条目数与分隔符不变，单条不超原长（字符硬闸）。
- 验收两件套缺一不可：事实保全审计（新旧集合差：引语/指针/日期/数字/路径）+ 指纹密度对照表；生产文件等主人点头才替换，先 `.bak`。

### Remediation loop (fixing a whole file's hard violations)

- Batch-rewrite by line number: run `--json`, group hard findings by line, build a Python dict `{line_no: new_line}`, apply it to `splitlines()` in one write, re-run the linter. Expect 3–4 converging rounds — semicolons and long sentences first (they dominate), then the tail. Replacing `；` with `。` clears both rules at once: the sentence splitter treats `；;` as terminators.
- Pre-check every replacement sentence with the linter's own `count_chars` before applying it — a candidate still over the limit costs a whole extra round. To load the linter as a module via `importlib.util.module_from_spec`, register it in `sys.modules` before `exec_module`, or its `@dataclass` definitions raise AttributeError.
- The linter ignores code: inline backticks, URLs, and markdown links are masked, fenced blocks skipped, table rows split into cells. Paths and commands inside backticks never count toward sentence length — don't shorten them.
- Budgeted files (memory stores with a hard char cap): the rewrite must be same-length or shorter. Check `len(text)` against the cap before installing the new file; exit code 0 and the char cap are both gates, and a rewrite that fits the rules but overflows the cap must be compressed, not installed.
- Exemption recursion: exemption registration lines quote the banned words and therefore hit the wordlist again. Register the recursion in one clause ("registration lines must cite the banned words to identify what is exempt") instead of chasing each new hit round by round.
- Only exempt what is genuinely a citation of the banned word (the word as discussion object, a definition being defined, or a substring of a coined term). Everything else gets rewritten; an exemption list that grows past a handful means the rewrite was lazy.

## Final Verify Pass

Treat [final-pass-checklist.md](./assets/final-pass-checklist.md) as a step you run, not a list you glance at. This is the lightest form of a generate → check → revise loop: one model, one conversation, no extra agents.

1. Re-read the rewrite against every checklist item.
2. Run the deterministic gate at the bottom of that file when you can use a shell: a one-line `grep` for the typographic tells and the fixed jargon list. It catches the exact strings self-review skims past. For Chinese text, additionally run `python3 ~/.hermes/scripts/ste-lint-zh.py <file>` (see Deterministic Chinese Gate above).
3. If any check fails, or the optional five-dimension score is below 35 / 50, do one targeted revision: fix only the flagged spots, do not rewrite the whole piece. Then re-check once.
4. Stop after at most two revision rounds. If something still fails on a real trade-off (a claim you cannot verify, a house style that genuinely wants the formatting), leave it and say so in the closing note.

In learning mode, add one check: compare the output's sentence rhythm and punctuation against the numbers recorded in the host profile, and nudge it back if it has drifted.

## Response Format

Return the revised text directly.

Add a short note only when one of these is true:
- The structure changed materially.
- Facts were ambiguous in the source.
- Proof is missing and the stronger version would require inventing it.
- The source asked for a very specific voice that conflicts with this skill.
- A non-default voice mode was used, so name it ("Ran in human-texture mode" / "Applied host profile X").

When adding a note, keep it to three lines or fewer.

If the user asks for critique rather than a rewrite, list the main sources of AI smell first, then show representative fixes.

## References

Scripts:
- [chunked_rewrite.py](./scripts/chunked_rewrite.py): 可直接跑的切片改写管道（直连 OpenAI 兼容端点、幂等断点续跑、行数守卫、shell 拼接、copy6 自检）——改开头 SRC/SP/输出路径常量即用

English-track:
- [patterns-to-remove.md](./references/patterns-to-remove.md): English phrases, structures, and formatting tells to strip out
- [before-after-benchmarks.md](./references/before-after-benchmarks.md): English regression-style examples
- [common-problems-and-fixes.md](./references/common-problems-and-fixes.md): Symptom-to-fix map
- [human-passes.md](./references/human-passes.md): Multi-pass editing workflow

Chinese-track:
- [chinese-patterns-to-remove.md](./references/chinese-patterns-to-remove.md): 中文 AI 文的词汇、句式、结构、语气痕迹
- [chinese-before-after.md](./references/chinese-before-after.md): 中文场景的前后对照基准

Voice modes:
- [human-texture.md](./references/human-texture.md): Optional irregularities for personal voice
- [learning-mode.md](./references/learning-mode.md): Sample-driven host profile workflow
- [scenario-presets.md](./references/scenario-presets.md): Per-scenario constraints (tweet, Weibo, Reddit, blog, podcast, report)

Assets:
- [final-pass-checklist.md](./assets/final-pass-checklist.md): Last review before returning copy
- [rewrite-prompt-template.md](./assets/rewrite-prompt-template.md): Reusable instruction block for other agents
- [host-profile-template.md](./assets/host-profile-template.md): Fillable template for learning mode
- [style-extraction-prompt.md](./assets/style-extraction-prompt.md): One-shot prompt to extract a host profile from samples
