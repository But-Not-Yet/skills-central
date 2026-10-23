# Statistical Power Claim Verification — Worked Example

## Incident

A colleague ("小嘴"/Qwen) proposed daily aggregation (n=365-730) and
claimed individual GPH test power would reach 55–75% at d=0.3.

## Re-derivation

```
n = 730 (3 years daily)
m = floor(n^0.5) = floor(27.0) = 27
SE = pi / sqrt(6 * m) = pi / sqrt(162) = 0.2466
t = d / SE = 0.3 / 0.2466 = 1.219

One-sided 5% test:
  P(reject | d=0.3) = P(Z > 1.645 - 1.219) = P(Z > 0.426)
  = 1 - Phi(0.426) ≈ 0.335  → ~33%

With bias-reduced GPH (SE reduced ~30%):
  SE ≈ 0.17, t ≈ 1.76
  P(Z > 1.645 - 1.76) = P(Z > -0.115) ≈ 0.546 → ~55%

So 55-75% is achievable ONLY with bias-reduced GPH at d≥0.3,
NOT with plain GPH. The original claim conflated bias-reduced and
plain GPH power.
```

## Corrected proposal text

```
SE≈0.25; d=0.3 时单个体检验功效约 20–25%，
d≥0.45 时可达 55–75%
```

## Propagation sweep

After correcting the number, grep ALL artifacts for the wrong value:
- `grep -rn "55.*75\|55-75" .tex .md .py` → fix each hit
- Check `power_analysis.py` defaults and docstrings
- Check `test_power_analysis.py` assertions
- Check notebook builder scripts

## General rule

Never copy a power/SE/n/threshold number from a colleague or reference
model into a proposal or test without re-deriving it from the formula.
The cost of a wrong number embedded in a submitted proposal is far
higher than the cost of a 2-minute calculation.
