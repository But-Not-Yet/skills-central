# Literature PDF Batch Download & Verification

Workflow for downloading all cited PDFs from a LaTeX proposal and verifying they are the *correct* papers, not look-alikes.

## Workflow

1. **Extract bibkeys**: `grep -o 'bibitem{[^}]*}' file.tex | sed 's/bibitem{//;s/}//'`
2. **Batch web_search** each paper: `"<author> <year> <title keywords> pdf"` — collect candidate URLs ranked by likelihood of being a direct PDF.
3. **Batch download** via `urllib.request` (in `execute_code`):
   - Headers: `User-Agent: Mozilla/5.0...`, `Accept: text/html,application/pdf,*/*`
   - `ssl._create_default_https_context = ssl._create_unverified_context` (academic sites often have incomplete SSL)
   - Timeout: 60s per URL
   - Try candidate URLs in priority order; stop on first `%PDF` response
4. **Magic bytes check** (Layer 1): `data[:4] == b'%PDF'` — rejects HTML login pages and error pages.
5. **Content verification** (Layer 2, CRITICAL): Run `pdftotext -f 1 -l 1 <file> -` and check first-page text against expected title/author/journal. **This layer catches wrong-paper downloads that pass magic bytes.**
6. **Delete wrong papers immediately** and re-mark as failed → triggers re-search in next batch.
7. **Status report**: Generate markdown table with columns: Bibkey | Status | Size | Source URL | Notes. For paywalled items, include the DOI URL so the user can access via institutional login.

## Source priority (highest success rate first)
1. arXiv preprints (`arxiv.org/pdf/<id>`)
2. Author homepages (`.edu` domains, personal sites)
3. long-memory.com and similar domain-specific mirrors
4. Open-access journals: MDPI, Frontiers, AIMS Press, T&F OA articles
5. Project Euclid (for IMS journals like *Annals of Statistics*)
6. EconStor / RePEc (for economics papers)
7. PubMed Central (for biomedical)

**Avoid**: Semantic Scholar PDF links (frequently 404), ResearchGate (403), Google Scholar cache (unreliable).

## Paywall patterns (cannot bypass without institutional access)
- **Wiley** (JTSA, J. Applied Econometrics): DOI redirects to Wiley Online Library, no free PDF
- **JSTOR / Econometrica Society**: Full-text behind login
- **Elsevier** (CSDA, J. Empirical Finance): ScienceDirect paywall
- **Springer** (older papers like Whittle 1953): Link.springer.com paywall
- **SSRN**: Requires free account registration
- **Taylor & Francis**: Some OA articles work; many return 403 to bots

Do NOT hammer 403 URLs repeatedly — risk IP ban. Try once, mark as paywalled, move on.

## CRITICAL PITFALL: Wrong-paper downloads

Magic bytes (`%PDF`) is **necessary but NOT sufficient**. Author homepages and institutional repositories frequently host *review/survey papers that cite the classic work*, not the classic work itself. These pass magic bytes but are the wrong paper.

### Verified real cases (2026-08-02 session)
| Expected | Downloaded instead | Source | Detection |
|----------|-------------------|--------|-----------|
| Geweke & Porter-Hudak 1983 (JTSA) | Kybernetika 1986 — Anděl "Long Memory Time Series Models" (a review citing GPH) | kybernetika.cz | pdftotext page 1 showed "KYBERNETIKA — VOLUME 22 (1986)" |
| Bai & Perron 1998 (Econometrica) | Yamamoto & Perron 2012 — "Estimating and Testing Multiple Structural Changes in Linear Models Using Band Spectral Regressions" | bu.edu/econ | pdftotext showed "Yamamoto" and 2012 date |
| Bai & Perron 2003 (J. Applied Econometrics) | Casini & Perron 2018 — "Structural Breaks in Time Series" (a handbook chapter) | bu.edu/econ | pdftotext showed "Casini" and 2018 date |
| Bhardwaj et al. 2024 (fractional state-space Kalman) | Chinellato & Marcuzzi 2024 — "State Estimation of Partially Unknown Dynamical Systems with a Deep Kalman Filter" (ICCS) | iccs-meeting.org | pdftotext showed "Chinellato" and "Deep Kalman Filter" |

### Why this happens
- Classic papers (1980s–1990s) were never posted as free PDFs; author pages link to *later* papers on the same topic.
- BU Economics department page hosts Perron's *recent* working papers, not his 1998/2003 classics.
- ICCS archive has *a* 2024 paper about Kalman filtering, not *the specific* Bhardwaj fractional-order paper.

### Prevention
- **Always run `pdftotext -f 1 -l 1` on every downloaded PDF** and eyeball the first 200 characters.
- Check: Does the first-page text contain the expected author surname and approximate year?
- If mismatch → delete the file, mark as paywalled/failed, do NOT keep the wrong paper.

## Python download + validation snippet

```python
import urllib.request, os, ssl, subprocess

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
           'Accept': 'text/html,application/pdf,*/*'}

def download_and_verify(bibkey, candidate_urls, pdf_dir, expected_surname, expected_year_range):
    filepath = os.path.join(pdf_dir, f"{bibkey}.pdf")
    for url in candidate_urls:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                if data[:4] != b'%PDF':
                    continue  # not a PDF, try next URL
                with open(filepath, 'wb') as f:
                    f.write(data)
                # Content verification
                result = subprocess.run(
                    ["pdftotext", "-f", "1", "-l", "1", filepath, "-"],
                    capture_output=True, text=True, timeout=30
                )
                text = result.stdout[:500]
                if expected_surname.lower() not in text.lower():
                    os.remove(filepath)  # WRONG PAPER — delete!
                    continue
                return {"status": "downloaded", "size_kb": len(data)//1024, "url": url}
        except Exception:
            continue
    return {"status": "failed", "url": candidate_urls[0] if candidate_urls else ""}
```
