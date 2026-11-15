# Mallarapu Yaswanth — Personal Portfolio

A static, multi-page professional portfolio for Mallarapu Yaswanth, published at [mallarapuyaswanth.me](https://mallarapuyaswanth.me/).

## Site structure

The root page is the main portfolio overview. Dedicated, clean-URL detail pages are published as folders containing an `index.html` file:

- `/projects/` — directory of project case studies.
- `/<project-slug>/` — individual project pages, with overview, scope, technology, source and live-demo links where verified.
- `/experience/` — detailed role history.
- `/honors-awards/` — awards, conferences and recognition.
- `/education/` — academic qualifications and scores.
- `/certificates/` — professional credentials and accreditations.

Shared detail-page layout and responsive navigation live in `assets/css/detail-pages.css` and `assets/js/detail-pages.js`. The main homepage continues to use its embedded design system and navigation script.

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

The suite checks metadata, unique IDs, internal links, local assets, image alternative text, external-link security attributes, JSON-LD, JavaScript syntax, sitemap and robots consistency, merge-conflict markers, detail-page canonical URLs, and page responsiveness. Browser tests cover 320px, 375px, 768px, 900px, 1024px and 1440px on the homepage and responsive checks across the detail routes. Screenshots are written to `test-results/`.

GitHub Actions runs the checks on pull requests and pushes to `main`, and uploads responsive screenshots as an artifact.

## Deployment

GitHub Pages serves the repository's `main` branch. The root `CNAME` file maps the deployment to `mallarapuyaswanth.me`. Folder-based `index.html` pages provide clean URLs such as `https://mallarapuyaswanth.me/bachelor-finance-manager/`. The XML sitemap lists the homepage and detail routes; `robots.txt` points crawlers to that sitemap.
