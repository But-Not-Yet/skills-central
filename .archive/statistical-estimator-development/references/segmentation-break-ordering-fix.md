# Segmentation Break Ordering Fix

## Problem

Binary segmentation for Bai-Perron structural break detection:
1. Find best single break in each segment (max SSR reduction)
2. Add to `break_candidates`
3. Sort `break_candidates` → compute BIC
4. Repeat

**Bug**: `break_candidates.sort()` after each addition reorders breaks by
*position*, not by *discovery order* (SSR reduction). When BIC selects
optimal `#breaks`, `break_candidates[:k]` gives first k by position,
not first k by importance.

**Result**: True break at t=100 found correctly, but returned as t=69
(sub-segment break from later iteration overwrote in positional order).

## Fix

Keep `break_candidates` in **discovery order** (by SSR reduction).
Only create sorted copy for BIC calculation.

```python
# Before (buggy)
break_candidates.append(best_new_break)
break_candidates.sort()
bic_scores.append(_bic_breaks(y, break_candidates))

# After (fixed)
break_candidates.append(best_new_break)
sorted_candidates = sorted(break_candidates)
bic_scores.append(_bic_breaks(y, sorted_candidates))
```

## Verification

```python
rr = np.random.default_rng(42)
y = np.concatenate([rr.normal(0, 1, 100), rr.normal(5, 1, 100)])
res = detect_breaks(y, max_breaks=3, min_segment=20)
# Before fix: res["breaks"] = [69]  ❌
# After fix:  res["breaks"] = [100] ✅
```

*Source: Session 2026-08-02, ARFIMA toolkit development*