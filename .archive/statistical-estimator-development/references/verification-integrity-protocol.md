# Verification Integrity Protocol — Reference

## MoA Snapshot Problem

MoA (Mixture of Agents) reference models read file snapshots that may
differ from current disk state. Observed discrepancy:

| Source | File size | GPH formula | MIT残留 | 6通道体系 |
|---------|-----------|------------|---------|-----------|
| Nemotron read_file | 49979 bytes | `d̂=-β̂₁/2` (wrong) | 0 (claimed) | present (claimed) |
| Disk (grep confirmed) | 48297 bytes | `d̂=-β̂₁/2` (wrong, pre-fix) | 4 (actual) | absent (actual) |

Nemotron read a **different version** of the file — possibly a cached
snapshot from an earlier point in the session. This caused 3 audit
items to be falsely marked "completed" when they were actually missing
from disk.

## Verification Checklist

When auditing whether a change list item is truly complete:

1. **Never trust reference model read_file** for go/no-go decisions.
   Use `terminal grep -n "keyword" "$FILE"` or your own `read_file`.

2. **Grep every claimed "completed" item**:
   ```bash
   TEX="/d/path/to/file.tex"
   echo -n "keyword: "; grep -c "keyword" "$TEX"
   ```
   If count = 0, the item is NOT on disk regardless of what any
   reference model claims.

3. **Cross-check file sizes**:
   ```bash
   wc -c "$FILE"
   ```
   If a reference model reports a different size, it read a stale
   snapshot — disregard its content claims entirely.

4. **Changelog review protocol**:
   When receiving a change list from an external agent (Qwen, another
   LLM):
   - Grep every "已完成" item against actual disk files
   - Check the change list itself for technical errors (wrong formula
     mappings, stale state assumptions)
   - In one session, the change list claimed `d̂=-β̂₁/2` was correct
     but the code used `d̂=-β̂₁` — the change list itself was wrong

5. **Post-patch grep for escape corruption**:
   ```bash
   # Double-backslash section
   grep -n '\\\\subsection\|\\\\section' "$TEX"
   # Line-split artifacts
   grep -n '^ef{\|^ef{' "$TEX"
   ```
   If found, fix via Python subprocess (not patch tool) to avoid
   re-corruption.

## Decision Rule

**Disk grep > read_file > reference model read_file**

Always escalate to the most direct source. A `grep -c` on the actual
file path is the ground truth. Reference model reads are hints, not
verification.

*Source: Session 2026-08-02/03, ARFIMA toolkit changelog review*
