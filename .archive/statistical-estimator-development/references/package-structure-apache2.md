# Apache 2.0 Scientific Python Package Template

## Directory Structure

```
package-name/
├── LICENSE                    # Apache 2.0 full text (copy from apache.org)
├── NOTICE                     # Copyright + attribution
├── pyproject.toml             # Build config (setuptools)
├── README.md                  # Module table, usage examples, license badge
├── src/
│   └── package_name/
│       ├── __init__.py        # Top-level exports (ALL public functions)
│       ├── module1.py         # Core estimators
│       └── ...
├── tests/
│   └── test_*.py             # Statistically grounded tolerances
└── notebooks/
    ├── _build_demo.py         # Build script (see notebook-building-pattern.md)
    └── 01_demo.ipynb          # Pre-executed demo notebook
```

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "package-name"
version = "0.1.0"
description = "One-line description"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.10"
dependencies = ["numpy>=1.24", "scipy>=1.10", "matplotlib>=3.7"]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[tool.setuptools.packages.find]
where = ["src"]
```

## __init__.py — Critical: Export Everything

```python
from package_name.module1 import func1, func2
from package_name.module2 import func3

__version__ = "0.1.0"
__all__ = ["func1", "func2", "func3"]
```

**Pitfall**: Forgetting to add a new function to `__init__.py` causes
`ImportError` when downstream code does `from package import func3`.

## NOTICE File

```
package-name
Copyright 2026 Author Name

This product includes software developed by Author Name (Affiliation).
This software is licensed under the Apache License, Version 2.0.
```

## Installation (Windows, bypass venv)

```bash
env -u VIRTUAL_ENV -u PYTHONPATH PATH="/c/Python313:/c/Python313/Scripts:/usr/bin:/c/Windows/System32" \
  /c/Python313/python.exe -m pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

*Source: Session 2026-08-02, ARFIMA toolkit development*