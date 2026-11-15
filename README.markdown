# Mallarapu Yaswanth — Personal Portfolio

A static, single-page professional portfolio for Mallarapu Yaswanth. The live site is published at [mallarapuyaswanth.me](https://mallarapuyaswanth.me/) from this repository.

## What the site contains

- Professional experience and selected engineering work
- Project summaries and live demonstrations
- Technical skills, awards, education, and certifications
- Direct email and telephone contact links
- A downloadable and browser-viewable PDF résumé
- Search and social-sharing metadata, including Schema.org JSON-LD

## Technology and runtime

The published site is a static HTML document. Its primary layout and responsive styles are embedded in `index.html`, and the active navigation/year/view-counter behavior is also embedded near the end of that file. There is no application server, database, or contact-form backend; visitors contact the owner through the listed email and telephone links.

The repository also retains standalone `styles.css`, `scripts.js`, and `xlsx.js` files from earlier experiments. They are not loaded by the current `index.html`. The JavaScript files are still syntax-checked so they remain safe to reuse or remove deliberately later.

External services currently referenced by the page include Google Fonts, Google tag/analytics, and the hits.sh profile-view badge. The core portfolio content and local résumé remain available if those services are blocked.

## Run locally

Python's built-in static server is sufficient; no build step is required:

```bash
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000).

## Quality checks

The repository includes static integrity checks and Playwright browser tests for desktop, tablet, and narrow mobile layouts.

```bash
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m unittest discover -s tests -v
```

The test suite checks document metadata, unique IDs, section links, local assets, image alternative text, secure external-link attributes, structured-data JSON, JavaScript syntax, sitemap/robots consistency, mobile menu behavior, browser errors, and horizontal overflow at 320px, 375px, 768px, 900px, 1024px, and 1440px viewport widths. Browser screenshots are written to `test-results/`.

GitHub Actions runs the same checks for pull requests and pushes to `main`.

## Deployment

GitHub Pages serves the repository's `main` branch. The root `CNAME` file maps the deployment to `mallarapuyaswanth.me`. Keep that file and the résumé/image assets in the repository root unless the corresponding paths in `index.html` are updated as part of the same change.
