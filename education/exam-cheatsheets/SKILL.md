---
name: exam-cheatsheets
description: "主人要考试速查表（cheatsheet、公式单页）时使用。"
version: 1.0.1
author: Hermes curator (Nekonya)
license: MIT
metadata:
  hermes:
    tags: [education, exam, latex, cheatsheet]
    related_skills: [latex-research-writing]
---

# Exam cheatsheets — skeleton-first, single page

## When to Use
- The user asks for an exam cheatsheet / review sheet / formula sheet, for any course or subject.
- The user asks to shrink, rewrite, or "make readable" an existing cheatsheet — the same rules apply.

## Hard rules
- **Skeleton, not answers.** The user derives on the exam; the sheet carries method skeletons plus pure-arithmetic lookups only. Delete final numerical answers, full per-problem derivations, and integral expansions. Hard budget: final text ≤ half of a full-transcription draft; prefer larger font over more content — a sheet too dense to read during the exam is worthless.
- **Gold standard = the user's own submitted solutions.** Verify every formula against their submitted HW/exam solution files before it goes on the sheet. External-AI solutions (other chatbots, chat exports) are claims to check, never sources to transcribe — they contain sign/direction errors; a caught mismatch is high-value output because it is exactly what the user would have copied wrong.
- **Browse course directories read-only**; deliver into a NEW standalone folder under the course directory.
- Sheet language: Chinese as location labels, math and technical terms in English (the exam itself is in English).

## Procedure
1. **Inventory (read-only).** `search_files` the course directory; find HW problem PDFs and the user's submitted solution `.tex`/`.pdf` files; read the solutions fully.
2. **Meta-analyze.** Per problem type extract exactly three things: (a) the universal starting formula every problem of that type begins from; (b) a per-problem budget table of intermediates that are pure arithmetic and slow to redo (per-distribution likelihood ratios, conditional-risk functions); (c) the derivation skeleton as numbered steps, imperative not prose.
3. **Assemble in lookup order:** type discrimination → universal starters → speed tables → per-problem budgets → proof skeletons → changed-numbers workflow + traps (especially lookalike problems whose parameters differ).
   - If the user says they are LOST in the material (illness, missed lectures — not just busy), restructure as a readable narrative instead of lookup order; dense lookup tables read as 杂乱 to a confused reader. Narrative form: one shared definitions block (every symbol defined exactly once, including symbols that appear only later, each with a one-line preview) → Bayes (definition in words → threshold formula → one-sentence why → numbered steps) → the hard method as THREE labeled directions — concept chain (theory), exam procedure (reverse order, the one actually walked), proof template — → proof toolkit → distribution→region-shape quick table → traps. Language-first: every formula labeled with its purpose in words; symbols only to define and for essential formulas.
4. **Cut pass.** Remove anything derivable on the exam in ≤2 min, then re-check the half-size budget. If page space remains, raise font size — legibility beats volume.
5. **Build.** Copy `templates/cheatsheet-main.tex` (single-page letter, 3-column, xeCJK) and fill sections. LaTeX compile gate and .tex pitfalls: see `latex-research-writing` — always also grep the log for "Missing character" (CJK-adjacent symbols silently drop).
6. **Notation pass.** Symbol friction is the top comprehension killer on a sheet read under exam stress. One role = one symbol across the whole sheet — never let one quantity wear three names (a decision threshold once carried t / y* / c in the same file). Quantities on different axes get different symbols, with the correspondence stated once: τ lives on the Λ axis (decide Λ≷τ), t on the y axis (region boundary), joined at the boundary by Λ(t)=τ. Register in the definitions block every symbol that appears only later (risk curve V, least-favorable prior, cost ratio, boundary threshold), each with a one-line preview, so nothing "suddenly appears" mid-sheet. Spell symbols exactly as the user's own handwritten solutions spell them (their comma subscripts, their calligraphic set letters) — the sheet gets hand-transcribed, and matching spelling removes all doubt. Before delivery, grep the .tex for legacy spellings' residue; a naive character-class check over-counts because the \mathcal prefix ends in a space — use lookbehind: `grep -oP '(?<!mathcal )T_1'`.
7. **Verify.** `latexmk -xelatex -interaction=nonstopmode -halt-on-error`; `pdfinfo` → Pages: 1 and letter size; log greps `^!` → 0 and `Missing character` → 0; `pdftotext` → section-header count matches plan (pdftotext scrambles 3-column CJK lines — grep per keyword, don't panic on 0s for strings that may be split across lines). One page is a hard constraint: if 2 pages, cut content, not font size.
8. **Font-escalation loop** (ESE 5280 midterm, proven): a lean skeleton leaves the page half-empty — wasted legibility. Rasterize `pdftoppm -png -r 60`, measure last-ink-row vs page height with PIL (use execute_code's python for PIL; terminal python may lack it); if <85%, raise `\fontsize` and recompile; stop when ~90–98% filled or before a 2nd page. ESE 5280 v4: content freed by the cut let 6.4pt → 11pt/13.2 at 98% fill, still one page — nearly double the reading size.
9. **Deliver.** PDF + .tex via MEDIA:. Report what was cut/kept and why, and walk ONE problem through the sheet's skeleton end-to-end to prove no step requires memorized knowledge.

## Pitfalls
- 课程进度与选课状态住 `~/Documents/UPenn/欠账与必读_20261006.md`（唯一账本），不在 memory——做 cheatsheet 前先读那份。
- Circled digits ①–⑤ have no glyph once the Western main font (lmroman) takes over — they silently vanish; use ASCII (1)(2)(3) and confirm via the Missing-character log grep.
- patch into .tex: LaTeX commands in new_string need single backslashes; double-escaped commands compile-break.
- Read the user's submitted solutions line-by-line before transcribing any formula — skim-level reuse is how a reversed inequality slips through.
- When the user claims a sheet symbol contradicts theirs ("yours is reversed"), do NOT flip the convention on demand: read the course's definition sentence in the lecture source and the user's own submitted solutions verbatim first. If both agree with the sheet, the reversal is a spelling misread — adopt the user's spelling and pin a concrete anchor (which given cost value is the false alarm in a known problem) into the definitions line. Flipping a consistent convention contradicts their graded work and changes downstream numeric answers (the equalizer equation itself changes).
