"""Check links in the site pages and the Markdown docs.

Local files and in-page anchors must exist. With --external, each http(s) URL is
requested once. A 404 or 410 fails the run. A network error is printed and does
not fail the run, because a blocked request is not a broken link.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HREF = re.compile(r"\]\(([^)\s]+)\)")
FENCE = re.compile(r"```.*?```", re.S)
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist", "node_modules"}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag in {"img", "script", "link"} and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag in {"img", "script"} and attrs.get("src"):
            self.hrefs.append(attrs["src"])


def html_files():
    found = []
    for name in ("index.html", "research.html", "limitations.html", "reproducibility.html", "404.html"):
        found.append(os.path.join(ROOT, name))
    found.append(os.path.join(ROOT, "web", "ridi-update-check.html"))
    return found


def markdown_files():
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info")]
        for name in files:
            if name.endswith(".md"):
                found.append(os.path.join(folder, name))
    return found


def ids_in(path: str) -> set[str]:
    text = open(path, encoding="utf-8").read()
    return set(re.findall(r'\bid="([^"]+)"', text))


def check_local(source: str, target: str, errors: list[str]) -> None:
    path, _, anchor = target.partition("#")
    if path.startswith(("http://", "https://", "mailto:", "tel:")):
        return
    if not path:
        file_path = source
    else:
        file_path = os.path.normpath(os.path.join(os.path.dirname(source), unquote(urlsplit(path).path)))
    if not os.path.exists(file_path):
        errors.append(f"{os.path.relpath(source, ROOT)}: missing {target}")
        return
    if anchor and file_path.endswith((".html", ".md")):
        if file_path.endswith(".md"):
            text = re.sub(r"```.*?```", "", open(file_path, encoding="utf-8").read(), flags=re.S)
            slugs = set()
            for heading in re.findall(r"^#{1,6} +(.+?)\s*$", text, re.M):
                slug = re.sub(r"[^\w\- ]", "", heading.strip().lower(), flags=re.UNICODE).replace(" ", "-")
                slugs.add(slug)
            if anchor not in slugs:
                errors.append(f"{os.path.relpath(source, ROOT)}: no heading {anchor} in {os.path.relpath(file_path, ROOT)}")
        elif anchor not in ids_in(file_path):
            errors.append(f"{os.path.relpath(source, ROOT)}: no id {anchor} in {os.path.relpath(file_path, ROOT)}")


def external_urls() -> set[str]:
    urls = set()
    for path in html_files():
        parser = Links()
        parser.feed(open(path, encoding="utf-8").read())
        for href in parser.hrefs:
            if href.startswith(("http://", "https://")):
                urls.add(href.split("#", 1)[0])
    for path in markdown_files():
        text = FENCE.sub("", open(path, encoding="utf-8").read())
        for target in HREF.findall(text):
            if target.startswith(("http://", "https://")):
                urls.add(target.split("#", 1)[0])
    return urls


def check_external(errors: list[str], notes: list[str]) -> None:
    for url in sorted(external_urls()):
        request = Request(url, method="HEAD", headers={"User-Agent": "ridi-check-link-check"})
        try:
            with urlopen(request, timeout=12) as response:
                status = response.status
        except HTTPError as exc:
            status = exc.code
        except URLError as exc:
            notes.append(f"unverified {url} ({exc.reason})")
            continue
        if status in (404, 410):
            errors.append(f"{status} {url}")
        elif status >= 400:
            notes.append(f"unverified {url} (HTTP {status})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--external", action="store_true", help="also request http(s) links")
    args = parser.parse_args()
    errors: list[str] = []
    for path in html_files():
        collector = Links()
        collector.feed(open(path, encoding="utf-8").read())
        for href in collector.hrefs:
            if href.startswith(("mailto:", "tel:", "data:")):
                continue
            if href.startswith(("http://", "https://")):
                continue
            check_local(path, href, errors)
    for path in markdown_files():
        text = FENCE.sub("", open(path, encoding="utf-8").read())
        for target in HREF.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            check_local(path, target, errors)
    notes: list[str] = []
    if args.external:
        check_external(errors, notes)
    for note in notes:
        print(note, file=sys.stderr)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"link check: {len(html_files())} HTML files, local links and anchors agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
