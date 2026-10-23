---
name: multi-doc-sync
description: Sync changes across docs with backup and grep verification.
---

# Multi-Document Change Synchronization

Sync changes from a core document (e.g. research proposal) to derivative
documents (business plan, implementation spec, architecture diagram,
strategy report), ensuring consistency, accuracy, and verifiability.

## Trigger

- User says "backup the previous X, Y, Z, then make corresponding changes,
  maintain consistency and accuracy"
- One core document changes and derivatives need to follow
- Any task involving "the same fact appearing across multiple documents"

## Mandatory Pre-Steps

1. **Archive backup (user's hard rule)**: Before editing, copy every
   target file to `<name>_<version>_Archived.<ext>`. Never edit in-place
   without backup. Covers .tex / .md / .drawio / .pptx. PDF need not be
   backed up separately (recompilable from .tex source).

2. **Grep all documents at once**: Run a single grep pass across all
   target files for all change keywords. Build a baseline showing every
   hit with its line number. This is the map for the entire session.

3. **Classify every grep hit** before deciding to modify:

| Category | Example | Action |
|----------|---------|--------|
| Own strategy statement | Own product license, data source, algorithm stack | **Must sync** |
| Third-party fact | Literature review citing a dataset; third-party lib MIT license | Keep unchanged |
| Historical reference | Old paper genuinely used IBM HR dataset | Keep as-is |
| Needs positioning note | Same dataset used for product baseline vs research | Add qualifier, don't delete |

## Product vs Research Terminology Isolation (Critical Pitfall)

Injecting research terminology into product documents is a common error.
Real example from this session:

- WRONG: Product implementation spec L6 algorithm layer changed to
  "ARFIMA/GPH/Whittle (Phase 1)" — ARFIMA is a research tool, product
  Phase 1 actually uses XGBoost+SHAP.
- CORRECT: "XGBoost+SHAP (Phase 1) -> fractional-order(ARFIMA)/Kalman/
  TE/MPC (Phase 2)" — research model appears as Phase 2 capability
  source, product phrasing preserved.

**Principle**: Product documents keep product-phase phrasing. Research
terms appear only as "capability source" annotations, tracked by grep.

## grep Closed-Loop Verification (Mandatory at End)

Grepping one document != verification complete. Final pass must run a
closed-loop grep matrix:

```bash
# Count new keywords across all docs
for doc in file1.tex file2.tex file3.drawio; do
  echo "$doc:"; grep -c "Apache-2.0\|BSL 1.1" "$doc"
done

# Residual check (should only show intentionally retained items)
grep -n "MIT" file.tex | grep -vi "MIT Sloan\|MIT/Apache"
```

Verification matrix must show: new keywords present (count > 0), old
keywords replaced (count 0 or only intentionally retained), PDF/PPT
regenerated.

## LaTeX Compile Verification

- Chinese-path files must be copied to English path for compilation
  (GBK environment corrupts Chinese filenames):
  `rm -rf /tmp/latex_XX && mkdir -p /tmp/latex_XX && cp source.tex
  /tmp/latex_XX/main.tex && cd /tmp/latex_XX && xelatex
  -interaction=nonstopmode main.tex` x 3 passes.
- After compilation, sync PDF back to original directory.
- When introducing new environments (e.g. `tabularx`), check file header
  for `\usepackage` — "Environment XXX undefined" = missing package.

## Audit Discipline: Disk Truth Over Everything

MoA reference models may return **stale session snapshots** instead of
current disk state. Real incident this session: a reference model read a
49979-byte version of a .tex file while the actual disk file was 49259
bytes — completely different content. This caused 3 audit items to be
falsely marked "completed" when they were missing.

**Iron rules**:
1. For any "does content X exist in file Y" decision, use terminal grep
   or your own read_file against the actual disk path. Reference model
   read_file outputs are hints, not evidence.
2. If reference model and disk state conflict, disk wins. Note the
   discrepancy in the report.
3. Audit reports must separate "grep evidence" from "inference" — never
   write inference as fact.

## External Changelist Review Protocol

When receiving a change list from an external agent (e.g. Qwen/小嘴),
grep every claimed "completed" item against the actual file before
executing. The change list itself may contain:
- Technical errors (wrong formula mappings, stale state assumptions)
- Items marked "done" that don't exist on disk
- Formula/paper-code inconsistencies not flagged by the author

Process: read changelist -> grep each claim -> mark genuine vs missing
-> execute only on confirmed gaps -> report discrepancies to user.

## Final Report Structure

1. Backup confirmation table (original <-> archived)
2. Per-document modification list (location, change, rationale)
3. grep closed-loop verification matrix
4. Compile verification results (page count, 0 errors)
5. Consistency check pass items
6. Explicit list of "intentionally retained residuals" (third-party
   licenses, literature review citations)

## Institutional Affiliation Cleanup (Compliance Pattern)

When the user says "delete all references to institution X" across the
workspace, this is a **compliance cleanup** — broader than normal doc
sync. It requires scanning every file (including backups, generated
metadata like egg-info, and binary formats like .pptx), not just the
files you remember editing.

Key differences from normal sync:
- **PPT**: grep won't find text in .pptx (binary). Use python-pptx
  run-level replacement via subprocess (preserves formatting).
- **egg-info**: After changing pyproject.toml author metadata, the
  stale `PKG-INFO` still contains old email. Delete + `pip install -e .`.
- **False positives**: Short abbreviations like "osu" appear in common
  words (e.g. "Disclosure"). Use `\b` word boundaries in grep, then
  manually inspect each hit.
- **PDFs**: Must recompile ALL .tex files whose source changed — old
  PDFs still show the deleted text.
- **Backup files**: User said "delete ALL" → patch archived copies too.

See `references/institutional-affiliation-cleanup.md` for the full
step-by-step workflow, replacement patterns, and judgment points to
flag for the user.

## References

- `references/latex-patch-gotchas.md` — Patch tool escape/linebreak
  traps and reliable fix patterns when editing .tex files.
- `references/institutional-affiliation-cleanup.md` — Full-folder
  compliance cleanup workflow: grep → archive → patch (incl. PPT
  run-level + egg-info) → recompile → closed-loop verify with
  false-positive exclusion.

## Overlap Note

The `statistical-estimator-development` skill covers ARFIMA/GPH/Whittle
implementation pitfalls (slope mapping, bias-reduction collinearity,
AR/MA polynomial form). This skill covers the **document synchronization
workflow** around those changes. They are complementary, not duplicative.
