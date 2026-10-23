# LaTeX Patch Tool Escape/Linebreak Traps

Real incidents from editing .tex files via the `patch` tool. Each entry
has symptom, root cause, and a reliable fix pattern.

## 1. Double backslash: `\subsection` → `\\subsection`

**Symptom**: After patch, `\subsection` becomes `\\subsection`. LaTeX
treats `\\` as an explicit line break, corrupting the document.

**Root cause**: Patch tool / JSON escaping interaction doubles backslashes
in certain code paths.

**Fix**: Do NOT retry with patch tool. Write a temp Python script:
```python
with open(tex_path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(r'\\subsection', r'\subsection')
# Also check \\section, \\begin, \\end, \\item
with open(tex_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

**Verify**: `grep -c '\\\\subsection' file.tex` must return 0.

## 2. `\S\ref{...}` line-break split

**Symptom**: `\S\ref{sec:method}` gets split into two lines:
`\S` + newline + `ef{sec:method}`. The `\r` or `\n` inside the JSON
string literal becomes a real line break in the file.

**Fix**: Python script, handle both `\n` and `\r\n`:
```python
content = content.replace('\\S\nef{', '\\S\\ref{')
content = content.replace('\\S\ref{', '\\S\\ref{')  # in case already partial
```

**Verify**: `grep 'S.ref{sec:method}' file.tex` — should show the
complete `\S\ref{sec:method}` on one line.

## 3. Missing `\usepackage` for new environments

**Symptom**: `! LaTeX Error: Environment tabularx undefined.`

**Root cause**: Patch introduced a `tabularx` (or other environment) in
the document body, but the file header doesn't load the package.

**Fix**: Add `\usepackage{tabularx}` to the preamble. **Before** writing
any new environment, grep the header:
```bash
grep "usepackage.*tabularx" file.tex
```

**General rule**: Any `! LaTeX Error: Environment XXX undefined` or
`Undefined control sequence` after a patch → check if the needed package
is loaded in the preamble.

## 4. Chinese path compilation corruption

**Symptom**: `xelatex` on a file with Chinese characters in the path
reports GBK encoding errors or "file not found" on Windows (GBK locale).

**Fix**: Copy to English temp path, compile, sync PDF back:
```bash
rm -rf /tmp/latex_XX && mkdir -p /tmp/latex_XX
cp "<chinese-path>/file.tex" /tmp/latex_XX/main.tex
cd /tmp/latex_XX
xelatex -interaction=nonstopmode main.tex   # ×3 passes
cp main.pdf "<chinese-path>/file.pdf"
```

## 5. Three-pass compilation for cross-references

**Symptom**: `LaTeX Warning: Label(s) may have changed. Rerun to get
cross-references right.`

**This is normal**, not an error. Run xelatex 3 times. After the third
pass, verify:
```bash
grep "undefined" main.log   # should be 0
grep "Output written" main.log  # should show page count
```

## 6. Post-patch verification protocol

After ANY `.tex` patch, before compiling, run:
```bash
# Check for double-backslash residuals
grep -n '\\\\section\|\\\\subsection\|\\\\begin\|\\\\end' file.tex

# Check for line-split artifacts
grep -n 'ef{sec:' file.tex   # \S\ref split

# Check for missing packages (if new environments introduced)
grep "usepackage" file.tex | head -20
```

Fix all residuals BEFORE compiling. Compiling with broken LaTeX
commands wastes a full compile cycle (~30s each).
