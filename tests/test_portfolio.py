from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from functools import partial
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # Static checks still work when Playwright is not installed.
    sync_playwright = None


class PortfolioHTMLParser(HTMLParser):
    """Collect the document features needed by the integrity checks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.anchors: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.resources: list[str] = []
        self.meta: list[dict[str, str]] = []
        self.scripts: list[dict[str, object]] = []
        self._active_script: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}

        if values.get("id"):
            self.ids.append(values["id"])

        if tag == "a":
            self.anchors.append(values)

        if tag == "img":
            self.images.append(values)

        if tag == "meta":
            self.meta.append(values)

        if tag == "link" and values.get("href"):
            self.resources.append(values["href"])

        if tag in {"img", "script"} and values.get("src"):
            self.resources.append(values["src"])

        if tag == "script":
            self._active_script = {"attrs": values, "content": []}

    def handle_data(self, data: str) -> None:
        if self._active_script is not None:
            self._active_script["content"].append(data)  # type: ignore[union-attr]

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._active_script is not None:
            content = "".join(self._active_script["content"])  # type: ignore[arg-type]
            self._active_script["content"] = content
            self.scripts.append(self._active_script)
            self._active_script = None


def parse_portfolio() -> tuple[str, PortfolioHTMLParser]:
    source = INDEX.read_text(encoding="utf-8")
    parser = PortfolioHTMLParser()
    parser.feed(source)
    parser.close()
    return source, parser


class StaticIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source, cls.document = parse_portfolio()

    def test_document_has_accessible_metadata(self) -> None:
        self.assertRegex(self.source, r'<html\b[^>]*\blang=["\']en["\']')
        self.assertRegex(self.source, r"<title>[^<]{8,}</title>")
        self.assertTrue(
            any(
                meta.get("name", "").lower() == "description"
                and len(meta.get("content", "")) >= 50
                for meta in self.document.meta
            ),
            "A useful meta description is required.",
        )
        viewport = next(
            (
                meta.get("content", "")
                for meta in self.document.meta
                if meta.get("name", "").lower() == "viewport"
            ),
            "",
        )
        self.assertIn("width=device-width", viewport)
        self.assertNotIn("maximum-scale", viewport.lower())
        self.assertIn('href="#main-content"', self.source)

    def test_ids_and_in_page_links_are_valid(self) -> None:
        self.assertEqual(
            len(self.document.ids),
            len(set(self.document.ids)),
            "HTML IDs must be unique.",
        )
        known_ids = set(self.document.ids)
        for anchor in self.document.anchors:
            href = anchor.get("href", "")
            if href.startswith("#") and len(href) > 1:
                self.assertIn(href[1:], known_ids, f"Unresolved section link: {href}")

        for element in re_find_aria_controls(self.source):
            self.assertIn(element, known_ids, f"aria-controls points to missing id: {element}")

    def test_local_assets_and_links_exist(self) -> None:
        for url in self.document.resources:
            parsed = urlparse(url)
            if parsed.scheme or parsed.netloc:
                continue
            relative_path = unquote(parsed.path).lstrip("/")
            if not relative_path:
                continue
            target = ROOT / relative_path
            if target.is_dir():
                target = target / "index.html"
            self.assertTrue(target.is_file(), f"Missing local resource: {url}")

        for anchor in self.document.anchors:
            href = anchor.get("href", "")
            if not href or href.startswith("#"):
                continue
            parsed = urlparse(href)
            if parsed.scheme or parsed.netloc:
                continue
            relative_path = unquote(parsed.path).lstrip("/")
            if relative_path:
                target = ROOT / relative_path
                if target.is_dir():
                    target = target / "index.html"
                self.assertTrue(
                    target.is_file(),
                    f"Missing local link target: {href}",
                )

    def test_images_and_external_link_security(self) -> None:
        for image in self.document.images:
            self.assertTrue(image.get("alt", "").strip(), f"Image needs alt text: {image}")

        for anchor in self.document.anchors:
            if anchor.get("target", "").lower() == "_blank":
                rel = set(anchor.get("rel", "").lower().split())
                self.assertIn("noopener", rel, f"Missing rel=noopener: {anchor.get('href')}")
                self.assertIn("noreferrer", rel, f"Missing rel=noreferrer: {anchor.get('href')}")

    def test_structured_data_is_valid_json(self) -> None:
        json_scripts = [
            script
            for script in self.document.scripts
            if script["attrs"].get("type", "").lower() == "application/ld+json"  # type: ignore[union-attr]
        ]
        self.assertTrue(json_scripts, "Expected Schema.org JSON-LD.")
        for script in json_scripts:
            json.loads(script["content"])  # type: ignore[arg-type]

    def test_all_javascript_files_and_inline_scripts_parse(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for JavaScript syntax checks.")

        for script_path in sorted(ROOT.rglob("*.js")):
            result = subprocess.run(
                [node, "--check", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"JavaScript syntax error in {script_path.name}:\n{result.stderr}",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            for index, script in enumerate(self.document.scripts):
                attrs = script["attrs"]  # type: ignore[assignment]
                if attrs.get("src") or attrs.get("type", "").lower() == "application/ld+json":
                    continue
                source = str(script["content"]).strip()
                if not source:
                    continue
                temp_file = Path(temp_dir) / f"inline-{index}.js"
                temp_file.write_text(source, encoding="utf-8")
                result = subprocess.run(
                    [node, "--check", str(temp_file)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"Inline JavaScript syntax error:\n{result.stderr}",
                )


    def test_portfolio_detail_pages_and_sitemap(self) -> None:
        import xml.etree.ElementTree as ET

        detail_pages = sorted(
            path for path in ROOT.glob("*/index.html")
            if path.parent != ROOT and path.name == "index.html"
        )
        self.assertGreaterEqual(len(detail_pages), 28, "Expected project and category detail pages.")

        expected_routes = {f"/{path.parent.name}/" for path in detail_pages}
        for page_path in detail_pages:
            source = page_path.read_text(encoding="utf-8")
            self.assertRegex(source, r"<title>[^<]{8,}</title>", page_path.as_posix())
            self.assertRegex(source, r'<h1\b[^>]*>[^<]{3,}</h1>', page_path.as_posix())
            self.assertRegex(
                source,
                rf'<link rel="canonical" href="https://mallarapuyaswanth\.me/{page_path.parent.name}/">',
                page_path.as_posix(),
            )
            parser = PortfolioHTMLParser()
            parser.feed(source)
            parser.close()
            self.assertEqual(
                len(parser.ids), len(set(parser.ids)),
                f"Duplicate ids on {page_path.parent.name}",
            )
            self.assertTrue(
                any(resource == "/assets/css/detail-pages.css" for resource in parser.resources),
                f"Shared CSS missing from {page_path.parent.name}",
            )

        sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = {
            node.text
            for node in sitemap.findall("sm:url/sm:loc", namespace)
        }
        self.assertIn("https://mallarapuyaswanth.me/", locations)
        for route in expected_routes:
            self.assertIn(
                f"https://mallarapuyaswanth.me{route}",
                locations,
                f"Route missing from sitemap: {route}",
            )

    def test_homepage_links_to_detail_hubs_and_project_cases(self) -> None:
        required_links = [
            'href="/projects/"',
            'href="/experience/"',
            'href="/honors-awards/"',
            'href="/education/"',
            'href="/certificates/"',
            'href="/bachelor-finance-manager/"',
            'href="/indian-dance-classification/"',
            'href="/ejite-journal-management-system/"',
            'href="/learn-norwegian/"',
            'href="/webrtc-voice-chat/"',
            'href="/python-terminal-games/"',
        ]
        for link in required_links:
            self.assertIn(link, self.source, f"Homepage is missing detail-page link: {link}")

    def test_sitemap_robots_and_repository_hygiene(self) -> None:
        import xml.etree.ElementTree as ET

        sitemap_path = ROOT / "sitemap.xml"
        sitemap = ET.parse(sitemap_path).getroot()
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [
            node.text
            for node in sitemap.findall("sm:url/sm:loc", namespace)
        ]
        self.assertIn("https://mallarapuyaswanth.me/", locations)
        self.assertEqual(len(locations), len(set(locations)), "Sitemap URLs must be unique.")
        self.assertGreater(len(locations), 20, "Sitemap should include the new detail routes.")

        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://mallarapuyaswanth.me/sitemap.xml", robots)

        readme = (ROOT / "README.markdown").read_text(encoding="utf-8")
        for marker in ("<<<<<<<", "=======", ">>>>>>>"):
            self.assertNotIn(marker, readme, f"Unresolved merge marker: {marker}")


def re_find_aria_controls(source: str) -> list[str]:
    import re

    return [
        controlled_id
        for match in re.finditer(r'\baria-controls=["\']([^"\']+)["\']', source, re.I)
        for controlled_id in match.group(1).split()
    ]


@unittest.skipIf(sync_playwright is None, "Install requirements-test.txt to run browser checks.")
class ResponsiveBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results_dir = ROOT / "test-results"
        cls.results_dir.mkdir(exist_ok=True)
        handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "browser"):
            cls.browser.close()
        if hasattr(cls, "playwright"):
            cls.playwright.stop()
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()

    def new_local_page(self):
        page = self.browser.new_page()
        page.route(
            "**/*",
            lambda route: route.continue_()
            if route.request.url.startswith(self.base_url)
            else route.abort(),
        )
        return page

    def test_layout_has_no_horizontal_overflow_across_viewports(self) -> None:
        page = self.new_local_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        viewports = [
            (320, 740),
            (375, 812),
            (768, 1024),
            (900, 800),
            (1024, 768),
            (1440, 900),
        ]
        try:
            for width, height in viewports:
                page.set_viewport_size({"width": width, "height": height})
                page.goto(self.base_url, wait_until="domcontentloaded")
                page.wait_for_timeout(150)
                dimensions = page.evaluate(
                    """() => ({
                        viewport: document.documentElement.clientWidth,
                        content: document.documentElement.scrollWidth
                    })"""
                )
                self.assertLessEqual(
                    dimensions["content"],
                    dimensions["viewport"] + 1,
                    f"Horizontal overflow at {width}px: {dimensions}",
                )

                if width <= 960:
                    self.assertTrue(
                        page.locator(".hero-photo-wrap").is_visible(),
                        f"Profile portrait should remain visible at {width}px.",
                    )

                page.screenshot(
                    path=str(self.results_dir / f"portfolio-{width}px.png"),
                    full_page=True,
                )

            local_image_results = page.locator("img").evaluate_all(
                """images => images
                    .filter(image => new URL(image.src).origin === location.origin)
                    .map(image => ({src: image.getAttribute('src'), width: image.naturalWidth}))"""
            )
            self.assertTrue(local_image_results, "Expected at least one local image.")
            for image in local_image_results:
                self.assertGreater(image["width"], 0, f"Local image did not load: {image['src']}")

            self.assertEqual(errors, [], f"Browser JavaScript errors: {errors}")
        finally:
            page.close()

    def test_mobile_navigation_open_close_escape_and_link(self) -> None:
        page = self.new_local_page()
        try:
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(self.base_url, wait_until="domcontentloaded")

            button = page.locator(".mobile-hamburger")
            menu = page.locator(".nav-menu")
            self.assertTrue(button.is_visible())
            self.assertFalse(menu.is_visible())
            self.assertEqual(button.get_attribute("aria-expanded"), "false")

            button.click()
            self.assertTrue(menu.is_visible())
            self.assertEqual(button.get_attribute("aria-expanded"), "true")
            self.assertTrue(
                page.locator("body").evaluate("(element) => element.classList.contains('mobile-menu-open')")
            )

            page.keyboard.press("Escape")
            self.assertFalse(menu.is_visible())
            self.assertEqual(button.get_attribute("aria-expanded"), "false")
            self.assertFalse(
                page.locator("body").evaluate("(element) => element.classList.contains('mobile-menu-open')")
            )

            button.click()
            page.locator('.nav-menu a[href="#projects"]').click()
            self.assertEqual(page.evaluate("window.location.hash"), "#projects")
            self.assertFalse(menu.is_visible())
            self.assertEqual(button.get_attribute("aria-expanded"), "false")

            page.set_viewport_size({"width": 1440, "height": 900})
            self.assertFalse(button.is_visible())
            self.assertTrue(menu.is_visible())
        finally:
            page.close()

    def test_detail_pages_render_without_overflow_on_mobile_tablet_and_desktop(self) -> None:
        page = self.new_local_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        route_pages = sorted(
            f"/{path.parent.name}/"
            for path in ROOT.glob("*/index.html")
            if path.parent != ROOT
        )
        try:
            for width in (320, 768, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                for route in route_pages:
                    response = page.goto(self.base_url.rstrip("/") + route, wait_until="domcontentloaded")
                    self.assertIsNotNone(response, f"No HTTP response for {route}")
                    self.assertEqual(response.status, 200, f"Page failed to load: {route}")
                    self.assertTrue(page.locator("main h1").is_visible(), f"Missing page heading: {route}")
                    dimensions = page.evaluate(
                        """() => ({
                            viewport: document.documentElement.clientWidth,
                            content: document.documentElement.scrollWidth
                        })"""
                    )
                    self.assertLessEqual(
                        dimensions["content"],
                        dimensions["viewport"] + 1,
                        f"Horizontal overflow at {width}px on {route}: {dimensions}",
                    )
            self.assertEqual(errors, [], f"Detail-page JavaScript errors: {errors}")
        finally:
            page.close()

    def test_detail_page_mobile_navigation_supports_escape_and_link_navigation(self) -> None:
        page = self.new_local_page()
        try:
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(self.base_url.rstrip("/") + "/projects/", wait_until="domcontentloaded")
            button = page.locator(".nav-toggle")
            menu = page.locator(".site-nav")
            self.assertTrue(button.is_visible())
            self.assertFalse(menu.is_visible())
            button.click()
            self.assertTrue(menu.is_visible())
            self.assertEqual(button.get_attribute("aria-expanded"), "true")
            page.keyboard.press("Escape")
            self.assertFalse(menu.is_visible())
            self.assertEqual(button.get_attribute("aria-expanded"), "false")
            self.assertEqual(page.evaluate("document.activeElement.className"), "nav-toggle")
            button.click()
            page.locator('.site-nav a[href="/experience/"]').click()
            self.assertTrue(page.url.endswith("/experience/"))
            self.assertFalse(menu.is_visible())
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
