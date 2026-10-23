# Notebook Building Pattern — Direct Execution + Capture

## Problem with exec()

Using `exec(compile(src, "<cell>", "exec"), ns)` with isolated `ns` causes:
- `NameError: name 'plt' not defined` — matplotlib imported at script top, not in `ns`
- `NameError: name 'matplotlib' not defined`
- Variable leakage between cells

## Solution: Direct Execution in Global Scope

All computation runs directly in the build script's global scope.
Capture stdout + figures for each logical "cell", assemble notebook JSON.

## Template

```python
import io, json, base64, sys, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "path/to/notebook.ipynb"
_nb_cells = []
_exec_count = [0]

def _md(src):
    _nb_cells.append({"cell_type": "markdown", "id": f"md-{len(_nb_cells)}",
                      "metadata": {}, "source": src.splitlines(keepends=True)})

def _code(src, captured_stdout, has_fig=True):
    _exec_count[0] += 1
    outputs = []
    if captured_stdout.strip():
        outputs.append({"output_type": "stream", "name": "stdout",
                        "text": captured_stdout.splitlines(keepends=True)})
    if has_fig:
        for figno in plt.get_fignums():
            fig = plt.figure(figno)
            png = io.BytesIO()
            fig.savefig(png, format="png", dpi=110, bbox_inches="tight")
            outputs.append({"output_type": "display_data",
                            "data": {"image/png": base64.b64encode(png.getvalue()).decode("ascii")},
                            "metadata": {}})
    plt.close("all")
    _nb_cells.append({"cell_type": "code", "id": f"code-{_exec_count[0]}",
                      "execution_count": _exec_count[0], "metadata": {}, "outputs": outputs,
                      "source": src.splitlines(keepends=True)})

# --- Define cell source strings as constants ---
SRC_IMPORTS = """import numpy as np
import matplotlib.pyplot as plt
print(f"numpy {np.__version__}")"""

SRC_CELL1 = """x = np.random.randn(100)
fig, ax = plt.subplots()
ax.plot(x)
print(f"Mean: {x.mean():.3f}")"""

# --- Execute in global scope, capture ---
_md("# Title")

old = sys.stdout; buf = io.StringIO(); sys.stdout = buf
print(f"numpy {np.__version__}")
sys.stdout = old
_code(SRC_IMPORTS, buf.getvalue(), has_fig=False)

old = sys.stdout; buf = io.StringIO(); sys.stdout = buf
x = np.random.randn(100)
fig, ax = plt.subplots()
ax.plot(x)
print(f"Mean: {x.mean():.3f}")
sys.stdout = old
_code(SRC_CELL1, buf.getvalue())

# --- Assemble & save ---
nb = {"cells": _nb_cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.13.3"}},
      "nbformat": 4, "nbformat_minor": 5}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
```

## Key Points

1. All imports at script top level — available to all cell computations
2. Source strings are constants — they become the notebook cell source
3. Figures captured via `plt.get_fignums()` — matplotlib state is global
4. `plt.close("all")` after each cell — prevents figure accumulation
5. Run build script with clean Python env (see SKILL.md Environment Note)

*Source: Session 2026-08-02, ARFIMA toolkit development*