# Mallarapu Yaswanth — Personal Portfolio

www.mallarapuyaswanth.me


## Content and source accuracy

Project pages are based on the public GitHub repositories and the existing portfolio entries. A live link is included only where a repository README or the current portfolio identifies a destination. Project pages state important scope limitations where relevant; for example, local-only storage, in-memory demo data, browser capability limits or the absence of a verified deployment URL.

The professional-profile website collection groups repositories whose pages describe other named professionals. Those subjects are not represented as the owner of this portfolio.

## Run locally

Python's built-in static server is sufficient; no build step is required:

```bash
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000).

## Quality checks

The repository includes Python static-integrity checks and Playwright browser tests.

```bash
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m unittest discover -s tests -v
```
