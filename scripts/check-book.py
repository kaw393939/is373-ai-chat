"""Validate the supported HTML edition without accessing external links."""

import argparse
import hashlib
import json
import subprocess
import threading
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "artifacts/book-html"


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.links = set(), []
        self.main, self.language = False, False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "html":
            self.language = attrs.get("lang") == "en"
        if tag == "main":
            self.main = True
        if tag == "img" and not attrs.get("alt"):
            raise ValueError("Book illustration needs a meaningful alt description")


def check():
    pages = {path.resolve(): Page(path.read_text()) for path in SITE.rglob("*.html")}
    if not pages:
        raise ValueError("Build the book first")
    for path, page in pages.items():
        if not page.main or not page.language or "content" not in page.ids:
            raise ValueError(f"Missing reading landmark/language/skip target: {path}")
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            destination = (path.parent / unquote(url.path)).resolve() if url.path else path
            if destination.is_dir():
                destination /= "index.html"
            if not destination.is_relative_to(SITE.resolve()) or not destination.exists():
                raise ValueError(f"Broken rendered link: {path.name} → {link}")
            if (
                url.fragment
                and destination in pages
                and unquote(url.fragment) not in pages[destination].ids
            ):
                raise ValueError(f"Broken rendered anchor: {path.name} → {link}")
    digest = hashlib.sha256()
    for path in sorted((ROOT / "book").rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(ROOT).as_posix().encode())
            digest.update(path.read_bytes())
    evidence = {
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        ),
        "book_tree_sha256": digest.hexdigest(),
        "html_pages": len(pages),
        "checks": [
            "local links and anchors",
            "language",
            "main landmark",
            "skip target",
            "image alternatives",
        ],
    }
    (ROOT / "artifacts/book-build.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"HTML checks passed: {len(pages)} pages; external URLs were not fetched.")


def browser():
    from playwright.sync_api import sync_playwright

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(SITE)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as p:
            client = p.chromium.launch()
            page = client.new_page()
            external = []
            page.on(
                "request",
                lambda request: (
                    external.append(request.url) if not request.url.startswith(base) else None
                ),
            )
            for path in sorted(SITE.rglob("*.html")):
                page.goto(base + "/" + path.relative_to(SITE).as_posix())
                assert page.locator("main h1").count() == 1, str(path)
                assert page.get_by_role("navigation", name="Book contents").count() == 1
            page.goto(base + "/generated/code-tours/")
            page.keyboard.press("Tab")
            assert page.locator(":focus").inner_text() == "Skip to chapter"
            page.keyboard.press("Enter")
            assert page.locator(":focus").get_attribute("id") == "content"
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path=str(ROOT / "artifacts/book-mobile.png"), full_page=True)
            assert external == [], external
            client.close()
        print(
            "Browser checks passed: all chapters, keyboard skip, mobile wrapping, offline assets."
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    check()
    if args.browser:
        browser()
