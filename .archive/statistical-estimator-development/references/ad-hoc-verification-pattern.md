# Ad-Hoc Verification Pattern — Fresh Evidence on Demand

## Purpose

Generate single-use verification scripts that run in a clean Python
environment, produce pass/fail evidence for specific code behaviors,
and self-clean. Not CI — provides ad-hoc confidence for recent changes.

## Template

```python
import os, subprocess, tempfile

script = r'''
import sys, json

passed = failed = 0
def ck(n, ok, info=""):
    global passed, failed
    if ok: passed += 1
    else:  failed += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {n}" + (f"  ({info})" if info else ""))

# --- VERIFICATION CHECKS ---
sys.path.insert(0, r"D:\path\to\package\src")
import package_name
ck("init_exports_func", hasattr(package_name, "func"))

# Artifact validity (e.g. notebook)
with open(r"D:\path\to\notebook.ipynb", encoding="utf-8") as f:
    nb = json.load(f)
code_cells = [c for c in nb["cells"] if c["cell_type"]=="code"]
errs = [c for c in code_cells for o in c.get("outputs",[]) if o.get("output_type")=="error"]
ck("notebook_zero_errors", len(errs)==0)

# Smoke test: end-to-end
import numpy as np
from package_name import simulate, estimate
x = simulate(1000, param=0.3, rng=np.random.default_rng(42))
result, se = estimate(x)
ck("smoke_recovers", abs(result-0.3)<0.15, f"d={result:.3f}")

# Multi-seed robustness (5+ seeds)
rj = sum(test(simulate(3000, 0.4, rng=np.random.default_rng(s)))["reject"]
         for s in [42, 99, 123, 2024, 7777])
ck("power_4of5", rj>=4, f"{rj}/5 reject")

print(f"\n{failed} failed, {passed}/{passed+failed} passed")
sys.exit(1 if failed else 0)
'''

path = os.path.join(tempfile.gettempdir(), "hermes-verify-xyz.py")
with open(path, "w", encoding="utf-8") as f:
    f.write(script)

env = dict(os.environ)
env.pop("VIRTUAL_ENV", None)
env.pop("PYTHONPATH", None)
env["PATH"] = r"C:\Python313;C:\Python313\Scripts;" + env.get("PATH", "")

try:
    res = subprocess.run([r"C:\Python313\python.exe", path],
                         capture_output=True, text=True, env=env, timeout=120)
    print(res.stdout)
    if res.stderr.strip():
        print("STDERR:", res.stderr[-500:])
    print("EXIT:", res.returncode)
finally:
    os.remove(path)
    print("Cleaned:", path)
```

## Key Elements

| Element | Purpose |
|---|---|
| `tempfile.gettempdir()` | OS-safe temp location |
| `env.pop("VIRTUAL_ENV")` | Bypass venv with broken packages |
| `subprocess.run(capture_output=True)` | Capture stdout/stderr |
| `finally: os.remove(path)` | Always clean up |
| Multi-seed robustness | Statistical checks use 5+ seeds |

## Verification Categories

1. **Changed-path checks** — Verify behaviors modified this session
2. **Artifact validity** — Generated files are well-formed
3. **Smoke/end-to-end** — Package imports and runs minimal pipeline

## Output Format

```
[PASS] init_exports_func
[PASS] smoke_recovers  (d=0.323)
0 failed, 11/11 passed
EXIT: 0
Cleaned: C:\Users\...\Temp\hermes-verify-xyz.py
```

> 以上为针对本次改动行为的 ad-hoc 临时验证（单次执行、已清理），非 CI 套件全绿声明。

*Source: Session 2026-08-02, ARFIMA toolkit development*