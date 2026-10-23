---
name: research-proposal-development
description: Review, revise, and LaTeX-ify academic research proposals.
---

# Research Proposal Development

Class-level skill for developing academic research proposals end-to-end: critical review (find fatal flaws), feasibility/value assessment, remediation planning through a multi-agent decision loop, revision under archive protocol, and production of LaTeX documents with academic rigor.

## When to use
- User asks to evaluate a scientific proposal/idea for holes, infeasibility, or value.
- User asks to revise a proposal (e.g. V2.1) and keep it consistent with approved plans.
- User asks to convert a markdown proposal to LaTeX with academic rigor, explicit math, and IEEE abbreviation conventions.
- Any academic document that will be compiled to PDF via LaTeX (Chinese content → XeLaTeX/ctex).

## Core workflow
1. **Hunt P0 (fatal) flaws before praising value.** In order:
   - **Toolchain runnability**: read every code snippet; verify imports/packages actually exist (real case: `from fracdiff import Fracdiff` and `statsmodels.tsa.arfima` are NOT valid Python — R-only / nonexistent; PyPI `fracdiff` is differencing-only, no MLE/GPH).
   - **Data semantics & cost**: verify with web_search (real case: GH Archive PushEvent counts pushes not commits — commit count is `payload.size`; PullRequestEvent needs `action='opened'`; bot filtering required; BigQuery cost estimates).
   - **Statistical traps**: spurious long memory from zero-inflation (Saha 2020; Granger & Hyung 2004); aggregation spurious long memory (Granger 1980) → individual-level analysis before group-level.
   - **Power analysis**: check whether claimed detection thresholds are reachable at planned sample sizes. Fix thresholds via simulation power analysis; publish the power curves.
   - **Literature gap claims**: soften absolute "zero precedent" claims; make precise boundary statements; list nearest neighbors with honest limitations.
2. **Multi-agent review loop**: Hermes (devil's advocate) → 小嘴/Qwen (meta-evaluator; catches over-pessimism) → user decides open questions → merge decisions into plan (`.hermes/plans/`).
3. **Archive protocol BEFORE modifying**: `cp file.ext file_V<x>.<y>_Archived.ext`, then edit.
4. **Consistency check after revision**: grep revised doc against every approved plan item; scan for residual v1 content (old thresholds, dead imports, old SQL, old timeline). Residual mentions are OK only as "v1 error, now fixed" annotations.
5. **LaTeX production**:
   - IEEE abbreviation rule (user requirement): first occurrence = full name (Abbreviation), thereafter abbreviation only.
   - Write every math expression explicitly as numbered equations — reach implementation level, no handwaving.
   - Verify every citation via web_search before writing (authors, year, venue, volume/pages).
   - Compile with **XeLaTeX** (ctex requires it). Never latexmk directly on Chinese paths — copy .tex to `/tmp/latex_build/main.tex`, run **3 passes** (cross-refs), copy PDF back.
   - `\argmin` etc. are NOT built-in LaTeX: add `\DeclareMathOperator*{\argmin}{arg\,min}`.
   - Re-derive every equation; classic errors: DM-test denominator needs sqrt of the HAC variance estimator.
   - Final QA: `grep -c "^!" main.log` == 0, `grep -c undefined main.log` == 0, all `\eqref` targets exist.
## User preferences (do not re-litigate)
   - NO pre-registration — user's stance: 先做着看 (work first, decide later). Remove all pre-registration content without asking.
   - Academic rigorous tone; refine "需要细化部分" to serious proposal depth.
   - Abbreviations: IEEE first-use-expansion rule (see above).
   - Open-source license preference: Apache 2.0 (not MIT — user changed from earlier proposal text).

## From proposal to Python implementation
When the user asks to implement the proposed statistical toolkit as a Python package:
1. **Package structure**: `src/` layout with `pyproject.toml`, `LICENSE` (Apache 2.0), `NOTICE`, `README.md`, `tests/`, `notebooks/`. Install with `pip install -e .`.
2. **Verify math before coding**: re-derive every formula from the proposal; check slope mappings and regressor forms against the spectral density (see GPH slope bug in pitfalls reference). Classic mistakes: wrong slope divisor (`-β/2` vs `-β`), collinear bias-reduction terms (`(log ω)^{k+1}` vs `ω^{2k}`), DM-test missing sqrt.
3. **Test tolerance calibration**: set recovery-test tolerances at **≈2 SE** based on the estimator's asymptotic SE formula, never razor-thin. GPH at n=5000: SE≈0.153 → tolerance 0.15. Whittle is tighter: tolerance 0.10. For hypothesis tests, use **multiple seeds** (≥5) and assert majority rejection, not single-seed.
4. **Ad-hoc verification**: after pytest passes, write a standalone verification script (in `tempfile.gettempdir()`, run with clean interpreter, clean up after) that exercises the core math fixes with known-parameter recovery checks. This catches bugs that pass unit tests but fail on the real math.
5. **Binary-segmentation ordering**: in Bai-Perron implementations, keep the working candidate list in detection order; sort a copy for BIC computation and final output. Re-sorting the working list picks sub-segment breaks over the global optimum.

## Literature PDF batch download & verification
After the LaTeX proposal is compiled, download all cited PDFs into a `literature review/pdfs/` folder:
1. Extract bibkeys: `grep -o 'bibitem{[^}]*}' file.tex | sed 's/bibitem{//;s/}//'`
2. Batch `web_search` each paper (`"<author> <year> <title keywords> pdf"`); collect candidate URLs.
3. Batch download via `execute_code` (urllib + `ssl._create_default_https_context = ssl._create_unverified_context`, UA headers, 60s timeout). Try candidate URLs in priority order (arXiv → author homepage → OA journal → Project Euclid → EconStor).
4. **Double validation — MANDATORY**:
   - Layer 1: magic bytes `data[:4] == b'%PDF'` (rejects HTML login pages).
   - Layer 2: `pdftotext -f 1 -l 1 <file> -` → check first-page text contains expected author surname + approximate year. **This catches wrong-paper downloads that pass magic bytes** (verified real cases: Geweke1983 → Kybernetika 1986 review; BaiPerron1998 → Yamamoto 2012; BaiPerron2003 → Casini 2018; Bhardwaj2024 → unrelated Deep Kalman paper). Delete mismatches immediately.
5. Generate status table (markdown): downloaded / paywalled / website. Paywalled rows must include DOI URL for institutional access. Do NOT hammer 403 URLs repeatedly (IP ban risk).
6. **Rename PDFs to `Bibkey_Paper_title_with_underscores.pdf`** (user requirement): preserves the bibkey prefix for greppable cross-reference with `.tex` `\cite{}` keys, followed by underscore-separated title. Example: `Hosking1981_Fractional_differencing.pdf`. Use `execute_code` with `os.rename()` — check for name collisions and non-existent source files before executing.
See `references/literature-pdf-download-verification.md` for full workflow, source-priority list, paywall patterns, wrong-paper case table, and Python download+validate snippet.

## Support files
- `references/arfima-long-memory-pitfalls.md` — verified knowledge bank: GPH math, bias-reduced variant, zero-inflation/aggregation traps, power numbers, Python toolchain facts, GH Archive SQL/cost facts, segmentation & DM-test formulas.
- `references/literature-pdf-download-verification.md` — batch PDF download workflow with double-validation (magic bytes + pdftotext content check), source-priority list, paywall patterns, and wrong-paper case table.
- `templates/academic-proposal-cjk-preamble.tex` — known-good ctexart preamble (packages, theorem environments, lstset, math operators) to copy and modify.

## Pitfalls
- Do NOT include pre-registration sections — user explicitly rejected it.
- If a write_file tool warns the file was previously read with pagination, re-read the whole file before overwriting.
- Don't ship LaTeX with undefined control sequences: grep `^!` in the log; run 3 xelatex passes so labels resolve; verify 0 undefined citations.
- Don't claim a package/estimator exists without checking (see real case above).
- **Wrong-paper downloads pass magic bytes**: Author homepages and institutional repos frequently host *later survey/review papers that cite the classic work*, not the classic itself. `pdftotext -f 1 -l 1` first-page extraction is the only reliable catch. Delete mismatches, do NOT keep the wrong paper.
- **Paywall patterns by publisher**: Wiley (JTSA, J. Applied Econometrics), JSTOR/Econometrica Society, Elsevier (CSDA, J. Empirical Finance), Springer (older papers), SSRN (account required), T&F (403 to bots). Try once, mark as paywalled with DOI URL, move on — don't risk IP ban.

## Overlap note
Overlaps with `research-proposal-review` (which covers only the review/audit phase). This skill is the broader umbrella; `research-proposal-review` is a subset that could be consolidated into it by the curator.