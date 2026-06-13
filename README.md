# patent-shared

Shared script library used as a **git submodule** by:

- [patent-mapping](https://github.com/jack-lee2022/patent-mapping) — mounted at `scripts/`
- [pro-patent-search](https://github.com/jack-lee2022/pro-patent-search) — mounted at `scripts/`

## Contents

| File | Purpose |
|------|---------|
| `google_patents_collector.py` | Google Patents XHR API search + Tor NEWNYM auto-rotation |
| `advanced/abstract_enricher.py` | Batch-enrich patents with abstracts and IPC codes (no count limit) |
| `advanced/ipc_classifier.py` | IPC-prefix-first tech/effect classifier with langdetect |
| `advanced/lang_utils.py` | Language detection (`is_english`, `build_classification_text`) |
| `advanced/visualizer.py` | 4-chart generator: assignee, trend, country, tech-effect matrix |
| `advanced/citation_crawler.py` | Citation snowball crawling |
| `advanced/claim_chart_gen.py` | Element-by-element claim chart vs. product description |
| `advanced/legal_status_calculator.py` | Patent expiry date and legal status calculation |
| `advanced/browser_renderer.py` | Playwright fallback renderer (when API is blocked) |
| `advanced/random_delay.py` | Human-like request delay to reduce blocking |

## Usage as submodule

```bash
# Add to a repo
git submodule add https://github.com/jack-lee2022/patent-shared scripts

# Clone a repo that uses this submodule
git clone --recurse-submodules <repo-url>

# Update to latest
git submodule update --remote scripts
```

## Tor Setup

`google_patents_collector.py` auto-rotates Tor exit node after 2 consecutive 503 responses.
Requires `torrc`:
```
SocksPort 9050
ControlPort 9051
CookieAuthentication 1
```
