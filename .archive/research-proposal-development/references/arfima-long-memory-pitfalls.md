# ARFIMA / Long-Memory Research: Verified Pitfall Bank

All facts verified via web search 2026-08. Re-verify when reusing in new contexts.

## GPH estimator (Geweke & Porter-Hudak 1983, JTSA 4(4):221-238)
- Periodogram: I(ω_j) = 1/(2πn) |Σ_t x_t e^{-iω_j t}|², ω_j = 2πj/n
- ARFIMA(0,d,0) spectrum (Taqqu et al. 1995, Fractals 3(4):785-798): f(ω) = σ²/(2π) · (2 sin(ω/2))^{-2d}; low-freq f(ω) ~ C|ω|^{-2d}
- GPH regression: log I(ω_j) = β₀ + β₁ log|1-e^{-iω_j}|² + u_j, j=1..m, m=⌊√n⌋
  - **Slope mapping (CRITICAL — verified by implementation 2026-08-02)**: since f(ω) = σ²/(2π)·(2sin(ω/2))^{-2d} and log|1-e^{-iω}|² = log(4sin²(ω/2)) = 2·log(2sin(ω/2)), the regression slope β₁ = **−d** (NOT −2d). Therefore **d̂ = −β̂₁** (NOT −β̂₁/2). Using −β̂₁/2 collapses estimates toward zero (d=0.3 → d̂≈0.08). If instead you regress on log(ω) directly (not log|1-e^{-iω}|²), THEN β₁ = −2d and d̂ = −β̂₁/2. Pick one regressor form and stay consistent.
- Asymptotics (Robinson 1995, Ann. Statist. 23(3):1048-1072): √m(d̂−d) → N(0, π²/6); SE = π/√(6m)
  - n=104 → m≈10 → SE≈0.405; n=400 → m=20 → SE≈0.287; n=512, m≈22 → SE≈0.274
- Bias-reduced GPH (Andrews & Guggenberger 2003, Econometrica 71(2):675-712): add Σ_{k=1}^{r} γ_k · ω_j^{2k} polynomial terms (r≥1) to absorb short-memory contamination.
  - **CRITICAL — verified by implementation 2026-08-02**: do NOT use (log ω_j)^{k+1} as the polynomial terms — they are **perfectly collinear** with the main regressor log|1-e^{-iω}|² at low frequencies (correlation = 1.000000), causing OLS coefficient explosion (d̂ ≈ 711 vs correct 0.05–0.26). The correct Andrews-Guggenberger form is ω_j^{2k} (frequency powers, not log-frequency powers). Condition number drops from 1.5×10⁵ to ~2.5×10³.
- Report bandwidth sensitivity; estimates are unstable across bandwidths on short series.

## Zero-inflation spurious long memory (CRITICAL for count data)
- Weekly commit counts: median developer >90% zero weeks. Zero-inflated, over-dispersed non-Gaussian data → GPH systematic positive bias → "spurious long memory".
- Saha et al. 2020, Cogent Econ. & Finance 8(1):1733280 — GPH pitfalls (spurious long memory, biases).
- Granger & Hyung 2004, J. Empirical Finance 11(3):399-421 — "occasional long memory" via structural breaks.
- Defensive design: two-stage zero model — active indicator Z_t ~ Bernoulli(π), intensity Y_t|Z_t=1 ~ ARMA(1,1). Simulate B=500 matched control series (same π, same marginal), run GPH on both, compare H₀:d=0 rejection rates (permutation p<0.05). Calibrate: H0 size = nominal ±0.02, BH-FDR q<0.05, monotone power surface. Single-point comparisons carry ~15% false-negative risk.

## Aggregation spurious long memory (Granger 1980)
- Heterogeneous short-memory AR(1) individuals aggregate into a process that LOOKS long-memory. ALWAYS estimate at the individual level first; group/subgroup analysis only as exploratory.

## Power trap
- With per-individual power 30–45% (d=0.3, SE≈0.2), a predefined threshold like ">40% individuals significant" may be unreachable even when memory is real. Determine τ* by simulating over a length × d × zero-rate grid and pick the reachable rejection rate at power ≥0.8; record threshold + achieved power. Power curves themselves become a methodology contribution.

## Test tolerance calibration (verified by implementation 2026-08-02)
- GPH finite-sample bias is ~0.1 even at n=5000 (d=0.3 → d̂=0.41; d=0.4 → d̂=0.52). Set recovery-test tolerances at **≈2 SE** (|d̂−d| < 0.15 at n=5000), never razor-thin (<0.1) — otherwise you chase Monte Carlo noise and get false test failures.
- Whittle MLE is tighter than GPH: d=0.3 → d̂=0.311 (|error|=0.01 vs GPH's 0.11); ARFIMA(1,0.2,0) with φ=0.5 → d̂=0.27, φ̂=0.43. Whittle tolerances can be stricter (0.10 for d, 0.20 for φ).
- Hypothesis-test checks: use **multiple seeds** (≥5) and assert **majority** rejection, not single-seed. GPH test for d=0.4 at n=5000: 4/5 seeds reject (one seed gives d̂=0.13 due to finite-sample variance — this is expected, not a bug).
- Power grid sanity: under H₀ (d=0), observed power should be ≤ α (observed 0.03 at α=0.05); power should be monotone increasing in d and decreasing in zero fraction.

## Python toolchain facts (2026-08)
- statsmodels: ARIMA/SARIMAX = integer d ONLY. No ARFIMA.
- PyPI `fracdiff`: fractional differencing operator only; no MLE/GPH.
- R standard: `fracdiff` (fdGPH, fdSperio, fracdiff MLE; Haslett & Raftery 1989) and `arfima` package — CRAN, Martin Maechler / Justin Veenstra.
- Self-implementation is feasible (~50-100 lines each):
  - GPH: FFT → periodogram → low-freq OLS (or local polynomial).
  - Whittle MLE: minimize Σ_j [log f(ω_j;θ) + I(ω_j)/f(ω_j;θ)]; L-BFGS-B with d∈(-0.5,0.5), |φ|<1; truncate (1-L)^d at K≈100 terms (error O(K^{-2d-1})); numba JIT for the scalar loops.
  - Simulator: x_t = Σ_{k=0}^{K} π_k ε_{t-k}, π_k = Γ(k−d)/(Γ(−d)Γ(k+1)).

## GH Archive / BigQuery facts
- Dataset ~17TB total (2011–2025). Three years of day.* tables ≈1–3TB per full scan.
- Pricing: $5/TB; 1TB/month free; new-user $300 credit → honest budget caps (~$50) needed.
- PushEvent counts pushes, NOT commits. Commit count = payload.size (JSON int) or payload.commits array length.
- PullRequestEvent includes opened/closed/merged/… → count only action='opened'.
- Bot filtering: actor.login NOT LIKE '%[bot]' PLUS explicit list (dependabot[bot], renovate[bot], github-actions[bot], greenkeeper[bot], snyk-bot, codecov[bot]).
- Payload JSON extraction on BigQuery is expensive (whole payload billed) — fine-tune queries on a day sample first.

## Segmentation & model comparison
- Bai & Perron 1998 Econometrica 66(1):47-78; 2003 J. Applied Econometrics 18(1):1-22 — max 3 breaks, BIC selection, per-segment estimation, Chow stability test.
- **Binary-segmentation ordering bug (verified by implementation 2026-08-02)**: in a sequential binary segmentation algorithm, breaks are found in SSR-reduction order (global optimum first, then sub-segment optima). If you `.sort()` the working candidate list after each iteration, BIC is computed on the right set BUT the returned `break_candidates[:k]` may pick a sub-segment break over the global optimum (returned [69] instead of true [100]). Fix: keep the working list in detection order; sort a COPY for BIC computation and for the final returned breaks list.
- Diebold-Mariano 1995 JBES 13(3):253-263: DM = ḡ / √(V̂(ḡ)), V̂(ḡ) = (1/T)(γ̂₀ + 2Σ_{k=1}^{h-1} γ̂_k) — HAC/Newey-West with truncation h−1. Missing sqrt is a classic error. DM →d N(0,1) under H₀.
- ARFIMA ACF: ρ(k) ~ C·k^{2d−1} (k→∞); fGn conversion d = H − ½ (NOT d = 1−α in general — α↔d depends on discretization; treat as "to be verified hypothesis" in proposals).
