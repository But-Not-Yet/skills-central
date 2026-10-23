---
name: exam-cheatsheets
description: 主人要考试速查表、公式单页、复习页时加载，把一张旧表改小改清楚同样适用这套规则。骨架先行、单页交付，附流程与易错点。
version: 1.0.1
author: Hermes curator (Nekonya)
license: MIT
metadata:
  hermes:
    tags: [education, exam, latex, cheatsheet]
    related_skills: [latex-research-writing]
---

# Exam cheatsheets: skeleton-first, single page

## When to Use
- The user asks for an exam cheatsheet / review sheet / formula sheet, for any course or subject.
- The user asks to shrink, rewrite, or "make readable" an existing cheatsheet. The same rules apply.

## Hard rules
- **Skeleton, not answers.** The user derives on the exam. The sheet carries method skeletons plus pure-arithmetic lookups only. Delete final numerical answers and full per-problem derivations. Also delete integral expansions. Hard budget: final text stays under half of a full-transcription draft. Prefer a larger font over more content. A sheet too dense to read during the exam is worthless.
- **Gold standard = the user's own submitted solutions.** Verify every formula against their submitted HW/exam solution files before it goes on the sheet. Treat external-AI solutions as claims to check, not sources to transcribe. Chatbot exports do contain sign and direction errors. A caught mismatch is high-value output: it is exactly what the user would have copied wrong.
- **Browse course directories read-only.** Deliver into a NEW standalone folder under the course directory.
- Sheet language: Chinese as location labels, math and technical terms in English (the exam itself is in English).

## Procedure
1. **Inventory (read-only).** `search_files` the course directory. Find HW problem PDFs and the user's submitted solution `.tex`/`.pdf` files, then read the solutions fully.
2. **Meta-analyze.** Per problem type, extract exactly three things. (a) The universal starting formula of that type. (b) A per-problem budget table of pure-arithmetic intermediates that are slow to redo, such as per-distribution likelihood ratios and conditional-risk functions. (c) The derivation skeleton as numbered steps. Write steps as commands, not prose.
3. **Assemble in lookup order:** type discrimination → universal starters → speed tables → per-problem budgets → proof skeletons → changed-numbers workflow + traps (especially lookalike problems whose parameters differ).
   - If the user says they are LOST in the material (illness, missed lectures, not just busy), restructure as a readable narrative instead of lookup order. Dense lookup tables read as 杂乱 to a confused reader. Narrative form, in this order. Open with one shared definitions block: every symbol defined exactly once, each with a one-line preview. Then Bayes: definition in words, threshold formula, one-sentence why, numbered steps. Then the hard method as THREE labeled directions: concept chain (theory), exam procedure (reverse order, the one actually walked), proof template. Then the proof toolkit. Then a distribution-to-region-shape quick table. Then traps. Language-first: label every formula with its purpose in words. Use symbols only in definitions and essential formulas.
4. **Cut pass.** Remove anything derivable on the exam in ≤2 min, then re-check the half-size budget. If page space remains, raise the font size: legibility beats volume.
5. **Build.** Copy `templates/cheatsheet-main.tex` (single-page letter, 3-column, xeCJK) and fill sections. For the LaTeX compile gate and .tex pitfalls see `latex-research-writing`. Always also grep the log for "Missing character": CJK-adjacent symbols silently drop.
6. **Notation pass.** Symbol friction is the top comprehension killer under exam stress. One role = one symbol across the whole sheet. Never let one quantity wear three names (a decision threshold once carried t / y* / c in one file). Give quantities on different axes different symbols, and state the correspondence once: τ lives on the Λ axis (decide Λ≷τ), t on the y axis (region boundary). They join at the boundary by Λ(t)=τ. Register every later-appearing symbol in the definitions block (risk curve V, least-favorable prior, cost ratio, boundary threshold), each with a one-line preview, so nothing "suddenly appears" mid-sheet. Spell symbols exactly as the user's handwritten solutions spell them (their comma subscripts, their calligraphic set letters). The sheet gets hand-transcribed, so matching spelling removes all doubt. Before delivery, grep the .tex for legacy spellings' residue. A naive character-class check over-counts, because the \mathcal prefix ends in a space. Use a lookbehind instead: `grep -oP '(?<!mathcal )T_1'`.
7. **Verify.** Run `latexmk -xelatex -interaction=nonstopmode -halt-on-error`. Check `pdfinfo` → Pages: 1 and letter size. Grep the log: `^!` → 0, `Missing character` → 0. Run `pdftotext` and match the section-header count to the plan. Beware: pdftotext scrambles 3-column CJK lines, so grep per keyword and never read a 0 as failure for a split string. One page is a hard constraint: if it runs to 2 pages, cut content, not font size.
8. **Font-escalation loop** (ESE 5280 midterm, proven). A lean skeleton leaves the page half-empty, which wastes legibility. Rasterize with `pdftoppm -png -r 60`. Measure the last-ink-row against page height with PIL, using execute_code's python (terminal python may lack PIL). If fill is under 85%, raise `\fontsize` and recompile. Stop at roughly 90–98% fill, or before a 2nd page. ESE 5280 v4: the cut freed content room and took 6.4pt to 11pt/13.2 at 98% fill, still one page. That is nearly double the reading size.
9. **Deliver.** PDF + .tex via MEDIA:. Report what was cut and what was kept, and why. Then walk ONE problem end-to-end through the sheet's skeleton, to prove no step requires memorized knowledge.

## Pitfalls
- 课程进度与选课状态住在 `~/Documents/UPenn/欠账与必读_20261006.md`（唯一记录），不在 memory 里。做 cheatsheet 之前先读那份。
- Circled digits ① through ⑤ have no glyph once the Western main font (lmroman) takes over: they silently vanish. Use ASCII (1)(2)(3), and confirm via the Missing-character log grep.
- patch into .tex: LaTeX commands in new_string need single backslashes. Double-escaped commands break the compile.
- Read the user's submitted solutions line-by-line before transcribing any formula. Skim-level reuse is how a reversed inequality slips through.
- When the user claims a sheet symbol contradicts theirs ("yours is reversed"), do NOT flip the convention on demand. First read, verbatim, the course's definition sentence in the lecture source and the user's own submitted solutions. If both agree with the sheet, the reversal is a spelling misread. Then adopt the user's spelling and pin a concrete anchor into the definitions line: state which given cost value is the false alarm in a known problem. Flipping a consistent convention contradicts their graded work. It also changes downstream numeric answers, because the equalizer equation itself changes.
