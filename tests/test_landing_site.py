"""Static landing contract. Browser interactions are separately smoke-tested in Edge."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = (ROOT / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
JS = (ROOT / "assets" / "site.js").read_text(encoding="utf-8")


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def parsed():
    parser = Tags()
    parser.feed(SITE)
    return parser.tags


def test_landing_is_not_old_redirect():
    assert 'http-equiv="refresh"' not in SITE.lower()
    assert "location.replace" not in SITE
    assert '<main id="main">' in SITE
    assert SITE.count("<h1") == 1
    assert 'lang="en"' in SITE
    assert 'dir="ltr"' in SITE


def test_assets_exist_and_no_external_runtime_dependencies():
    assert (ROOT / "web" / "ridi-update-check.html").is_file()
    for path in ["assets/site.css", "assets/site.js", "assets/favicon.svg", "assets/og-card.svg"]:
        assert (ROOT / path).is_file(), path
    for tag, attrs in parsed():
        if tag == "script" and "src" in attrs:
            assert attrs["src"].startswith("./assets/"), attrs["src"]
        if tag == "link" and attrs.get("rel") in {"stylesheet", "icon"}:
            assert attrs["href"].startswith("./assets/"), attrs
    assert "fetch(" not in JS and "XMLHttpRequest" not in JS


def test_every_arabic_translation_key_is_provided():
    keys = set(re.findall(r'data-i18n="([^"]+)"', SITE))
    keys.update(re.findall(r'data-i18n-aria="([^"]+)"', SITE))
    mapped = set(re.findall(r"^\s*(\w+)\s*:", JS, re.M))
    assert keys, "Missing translation markers"
    assert keys <= mapped, "Missing Arabic translations: " + ", ".join(sorted(keys - mapped))


def test_local_links_have_real_targets():
    count = 0
    for tag, attrs in parsed():
        if tag != "a":
            continue
        href = attrs.get("href", "")
        if href.startswith("#"):
            assert 'id="' + href[1:] + '"' in SITE, href
        elif href.startswith("./"):
            path = (ROOT / unquote(urlsplit(href).path)).resolve()
            assert path.is_relative_to(ROOT.resolve()), href
            assert path.is_file(), href
            count += 1
    assert count >= 4


def test_external_new_tab_links_are_safe():
    checked = 0
    for tag, attrs in parsed():
        if tag != "a":
            continue
        href = attrs.get("href", "")
        if href.startswith("https://") and attrs.get("target") == "_blank":
            rel = set(attrs.get("rel", "").split())
            assert {"noopener", "noreferrer"} <= rel, href
            checked += 1
    assert checked >= 6


def test_provenance_scopes_and_restrictions_are_visible():
    assert "43317397792" in SITE  # Signed same-weights configuration change
    assert "43312668253" in SITE  # Signed Qwen model substitution on BoolQ
    assert "43308859544" in SITE  # Synthetic signed release-gate proof
    assert "same_weights_prompt_update_20261113.md" in SITE
    assert "independent clinical validation" in SITE
    assert "published answer key" in SITE
    assert "--check-scores" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_small_screen_overflow_guards_are_present():
    assert ".ambient{position:fixed;" in CSS
    assert "inset:20px 0 0 0;" in CSS
    assert ".start-card{min-width:0;" in CSS
    assert ".start-grid{grid-template-columns:minmax(0,1fr);" in CSS
    assert "prefers-reduced-motion" in CSS
