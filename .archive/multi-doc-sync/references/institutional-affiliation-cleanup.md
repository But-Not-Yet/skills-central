# Institutional Affiliation Removal Pattern

When the user says "delete all OSU/institutional references" — this is a
**compliance cleanup**, not a normal content sync. It requires scanning
every file in the workspace, including backups and generated metadata.

## Step-by-Step Workflow

### 1. Full-folder grep (not just target files)

```bash
grep -rniE "ohio state|osu\.edu|\bosu\b|mechanical.*aerospace" \
  "$WORKSPACE" \
  --include="*.tex" --include="*.md" --include="*.py" --include="*.toml" \
  --include="*.drawio" --include="*.txt" --include="NOTICE" --include="LICENSE" \
  --include="*.json"
```

**Key**: scan the ENTIRE workspace, not just the files you remember editing.
Hits will appear in:
- Source files (.tex, .py, .md, .drawio)
- PPT generation scripts (.py) — the .pptx itself is binary, won't grep
- PPT text dumps (.txt)
- License/strategy docs (.md)
- Backup/archived files — **the user said "delete ALL", so backups too**
- Generated metadata (egg-info/PKG-INFO — contains author-email from pyproject.toml)
- Plans (.hermes/plans/) — usually clean, but check

### 2. PPT text — grep won't find it

.pptx is a binary (zip). Must use python-pptx to scan:

```python
from pptx import Presentation
prs = Presentation(pptx_path)
for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        def check(shape):
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        low = run.text.lower()
                        if 'osu' in low or 'ohio' in low:
                            print(f'Slide {i}: [{run.text}]')
            if shape.shape_type == 6:  # GROUP
                for child in shape.shapes:
                    check(child)
        check(shape)
```

### 3. PPT in-place replacement — run level, NOT paragraph level

**Critical**: `text_frame.text = new_text` destroys all formatting (fonts,
colors, sizes). Must replace at the **run level** to preserve formatting:

```python
def replace_in_runs(text_frame, old, new):
    for para in text_frame.paragraphs:
        for run in para.runs:
            if old in run.text:
                run.text = run.text.replace(old, new)

def deep_replace(shape, old, new):
    if shape.has_text_frame:
        replace_in_runs(shape.text_frame, old, new)
    if shape.shape_type == 6:  # GROUP
        for child in shape.shapes:
            deep_replace(child, old, new)
```

Run via subprocess to clean C:\Python313 (execute_code sandbox lacks
python-pptx):

```python
subprocess.run(
    [r"C:\Python313\python.exe", "-c", script],
    env={**os.environ, "VIRTUAL_ENV": "", "PYTHONPATH": "",
         "PATH": r"C:\Python313;C:\Python313\Scripts;C:\Windows\System32"}
)
```

### 4. egg-info regeneration

After changing `pyproject.toml` (e.g. removing author email), the old
`egg-info/PKG-INFO` still contains the stale metadata:

```bash
# Delete stale egg-info
rm -rf src/package.egg-info
# Regenerate
pip install -e . --no-build-isolation
# Verify
grep -i "osu" src/package.egg-info/PKG-INFO
```

If `pip install -e .` doesn't clean it fully, manually patch PKG-INFO.

### 5. False positive exclusion in grep

Short abbreviations like "osu" appear as substrings in common words:

| False positive | Why it matches | Fix |
|---|---|---|
| `Patent Disclosure` | Contains `osu` substring | Use `\bosu\b` word boundary, or `grep -v disclosu` |
| Base64 image data in .ipynb | Random byte sequences | Exclude .ipynb from grep, or `grep -v "base64"` |
| `MIT` in `submit`/`admit`/`commit` | Substring match | Use `\bMIT\b` or `grep -vi` known words |

**Rule**: Always use `-E` with `\b` word boundaries for short abbreviations.
After grep, manually inspect each hit to classify real vs false positive
before reporting "0 residuals".

### 6. Recompile ALL PDFs

PDFs compiled before the cleanup still show old text. Must recompile:
- Every .tex file that was modified → xelatex ×3 → sync PDF
- PPT changes don't need "recompilation" (saved in-place by python-pptx)

### 7. Closed-loop verification matrix

```python
# Text files
grep -rniE "ohio state|osu\.edu|\bosu\b" "$WS" --include=*.tex --include=*.md ...
# → must be 0 real hits (after excluding false positives)

# PPT (via subprocess python-pptx)
# → must be 0 hits

# PDFs (check timestamp freshness)
# → all PDFs must have post-cleanup mtime

# egg-info
# → PKG-INFO must not contain old email

# NOTICE file
# → no institution name

# pyproject.toml
# → authors list has no institution email
```

## Common Replacement Patterns

| Original | Replacement | Notes |
|---|---|---|
| `The Ohio State University` | `独立研究者` (or `Independent Researcher`) | Replace with user's preferred term |
| `Department of Mechanical & Aerospace Engineering` | Delete line entirely | Department = institution affiliate |
| `指导教师：Prof. X (OSU)` | Delete entire line, keep `作者：Mujing Li` | Or remove just `(OSU)` if user wants to keep advisor name |
| `(OSU, 2026, Honors Research Distinction)` | `(独立研究，2026)` | Or just remove parenthetical entirely |
| `OSU MSE · ` | Delete | Degree = institution affiliate |
| `不使用 OSU 的电脑/服务器/邮箱` | `不使用任何学校或单位的电脑/服务器/邮箱` | Generalize, don't name specific institution |
| `li.3958@osu.edu` | Remove email field entirely | Keep author name, drop institutional email |

## Judgment Points to Flag for User

Some replacements require user judgment — don't auto-decide:

1. **Advisor/co-author names**: If they're OSU professors but the user
   collaborated with them, removing names might misrepresent authorship.
   Flag for user decision.
2. **Thesis/dissertation attribution**: If the thesis was genuinely
   submitted to OSU, changing "The Ohio State University, 2026" to
   "独立研究，2026" may be factually incorrect. Suggest neutral phrasing
   like just removing the institution name.
3. **Committee members**: Names like "Goswami, Hereid" are OSU faculty
   but don't explicitly say "(OSU)". Removing them changes the document's
   completeness. Flag for user.
