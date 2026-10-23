---
name: statistical-estimator-development
description: Build statistical estimator toolkits in Python with tests.
---

# Statistical Estimator Toolkit Development

Build Python packages that implement statistical estimators for time-series
analysis, with emphasis on long-memory processes (ARFIMA, fractional integration).

## Core Module Pattern

| Module | Purpose | Key Implementation Notes |
|---|---|---|
| `simulator` | ARFIMA(p,d,q) generation | MA(∞) with truncated ψ_k = Γ(k+d)/(Γ(d)Γ(k+1)) |
| `gph` | Bias-reduced GPH estimator | **Slope on `log\|1-e^{-iω}\|²` is `-d` (NOT `-2d`)**. Bias-reduction uses `ω^{2k}` (Andrews & Guggenberger 2003), NOT `(log ω)^{k+1}` (perfectly collinear). |
| `whittle` | Whittle MLE (frequency domain) | Minimize ℓ_W = Σ[log f(ω) + I(ω)/f(ω)] over Fourier freqs. **AR/MA polynomials must use standard form** `φ(L) = 1 - Σφ_i·z^i` (NOT product form `∏(1-φ_i·z)` which is wrong for |φ|>1). |
| `zero_inflation` | Confounding test for zero-inflated counts | Two-stage hurdle (Bernoulli + AR(1)); simulate null distribution |
| `power_analysis` | Grid search for detection power | Vary (n, d, zero_fraction); find threshold τ* for target power |
| `segmentation` | Bai-Perron structural breaks | Binary segmentation + BIC; **keep break candidates in discovery order** (SSR reduction), sort only for BIC computation |

## GPH Estimator — Critical Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Wrong slope mapping | d_hat explodes (e.g. 711 for white noise) | `d_hat = -beta[1]` (not `/2`) — slope on `log\|1-e^{-iω}\|²` = `-d` |
| Collinear bias-reduction | poly_order≥1 gives huge/NaN | Use `ω^{2k}` as regressors, NOT `(log ω)^{k+1}` (corr=1.0 with main regressor) |
| Bandwidth choice | High variance or bias | Default `m = ⌊n^{0.5}⌋`; allow override |

See `references/gph-estimator-fixes.md` for full math derivation.

## Scientific Package Structure (Apache 2.0)

```
package/
├── LICENSE              # Apache 2.0 full text
├── NOTICE               # Copyright + attribution
├── pyproject.toml       # setuptools, deps
├── README.md            # Module table, usage examples
├── src/package/
│   ├── __init__.py      # ALL public functions exported at top level
│   └── *.py
├── tests/
│   └── test_*.py        # Statistically grounded tolerances
└── notebooks/
    ├── _build_demo.py   # Build script: direct execution → capture → assemble
    └── 01_demo.ipynb    # Pre-executed notebook with outputs + figures
```

**Pitfall**: Forgetting to export a function in `__init__.py` causes
`ImportError` downstream. Always add new public functions to `__init__.py`
and `__all__`.

See `references/package-structure-apache2.md` for full template.

## Notebook Building — Avoid exec()

**Problem**: `exec(compile(src, "<cell>", "exec"), ns)` with isolated `ns`
causes `NameError: name 'plt' not defined` — matplotlib/numpy imported at
script top level aren't in `ns`.

**Fix**: Run all computation directly in the build script's global scope.
Capture stdout via `io.StringIO()` redirect; capture figures via
`plt.get_fignums()` + base64 PNG. Assemble notebook JSON manually.

See `references/notebook-building-pattern.md` for full template.

## Test Tolerances — Statistically Grounded

GPH SE ≈ `π/√(6m)` where `m = ⌊n^{0.5}⌋`. For n=5000, m≈70, SE≈0.15:
- White noise: `abs(d_hat) < 0.30` (2σ)
- Recovery d=0.3: `abs(d_hat - 0.3) < 0.15` (finite-sample bias ~0.1)
- Whittle: smaller bias, `abs(d_hat - 0.3) < 0.10`

**Pitfall**: Arbitrary tight thresholds (e.g. 0.1 for GPH) will fail
~50% of seeds. Use multi-seed robustness (5+ seeds, require ≥4/5 reject)
for hypothesis-test checks.

## Segmentation — Break Ordering Fix

Binary segmentation must keep `break_candidates` in **discovery order** (by
SSR reduction). `break_candidates.sort()` after each addition reorders by
position — BIC selection then picks wrong breaks (e.g. returns t=69 when
true break is t=100).

Fix: `sorted_candidates = sorted(break_candidates)` only for BIC, keep
original list in discovery order.

See `references/segmentation-break-ordering-fix.md`.

## Verification Integrity — MoA Snapshots vs Disk Reality

**Critical lesson**: MoA (Mixture of Agents) reference models may read
**stale snapshots** of files, not current disk state. In one session,
Nemotron read a 49979-byte version of a .tex file while the actual disk
file was 48297 bytes — completely different content. This caused 3
audit items to be falsely marked "completed" when they were missing.

**Rule**: Never use reference model `read_file` outputs for go/no-go
verification decisions. Always confirm with direct `terminal grep` or
your own `read_file` call against the actual disk path.

**Changelog review protocol**: When receiving a change list from an
external agent (e.g. Qwen), grep every claimed "completed" item against
the actual file before executing. The change list itself may contain
technical errors (wrong formula mappings, stale state assumptions).

See `references/verification-integrity-protocol.md` for the full
checklist.

## LaTeX Patch Tool Escape Bugs

When using the `patch` tool on `.tex` files, backslash-heavy LaTeX
commands can be corrupted:

| Bug | Cause | Fix |
|---|---|---|
| `\S\ref{...}` → `\S\nef{...}` | JSON processing splits `\r` as line break | Use `skill_manage` or Python subprocess for complex LaTeX strings |
| `\subsection` → `\\subsection` | Patch tool doubles backslash | Post-patch grep for `\\\\(sub)?section` and fix via Python |

**Rule**: After any `.tex` patch, grep for double-backslash residuals
and `\n` line-split artifacts before compiling.

## Ad-Hoc Verification Pattern

Create temp scripts in `tempfile.gettempdir()`, run with clean Python env
(bypass venv), capture stdout, auto-clean. Not CI — provides ad-hoc
confidence for recent changes.

See `references/ad-hoc-verification-pattern.md` for template.

## Environment Note (Windows)

On this host, run Python scripts with:
```bash
env -u VIRTUAL_ENV -u PYTHONPATH PATH="/c/Python313:/c/Python313/Scripts:/usr/bin:/c/Windows/System32" \
  /c/Python313/python.exe <script>
```
This bypasses the hermes venv (broken numpy/PIL). Use pip mirror
`-i https://pypi.tuna.tsinghua.edu.cn/simple` for installs.
