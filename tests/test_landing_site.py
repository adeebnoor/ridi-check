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
    for path in ["assets/site.css", "assets/site.js", "assets/favicon.svg", "assets/og-card.svg", "assets/og-card.png"]:
        assert (ROOT / path).is_file(), path
    for tag, attrs in parsed():
        if tag == "script" and "src" in attrs:
            assert attrs["src"].startswith("./assets/"), attrs["src"]
        if tag == "link" and attrs.get("rel") in {"stylesheet", "icon"}:
            assert attrs["href"].startswith("./assets/"), attrs
    assert "fetch(" not in JS and "XMLHttpRequest" not in JS



def test_social_image_is_a_real_1200_by_630_png():
    """Social cards generally need raster images rather than an SVG-only Open Graph tag."""
    data = (ROOT / "assets" / "og-card.png").read_bytes()
    assert data[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10])
    import struct
    assert struct.unpack(">II", data[16:24]) == (1200, 630)
    assert 'assets/og-card.png' in SITE
    assert 'content="image/png"' in SITE


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


ROOT_PAGES = ["index.html", "research.html", "limitations.html", "reproducibility.html"]


def test_science_pages_state_the_manuscript_without_a_journal_claim():
    research = (ROOT / "research.html").read_text(encoding="utf-8")
    for page_name in ROOT_PAGES:
        text = (ROOT / page_name).read_text(encoding="utf-8")
        assert "Nature" not in text, page_name
        assert "accepted" not in text.lower(), page_name
        assert "gtag" not in text and "google-analytics" not in text and "plausible" not in text
    for needed in (
        "10.17605/OSF.IO/7UZV5",
        "10.17605/OSF.IO/ANBJD",
        "osf.io/7uzv5",
        "osf.io/anbjd",
        "Manuscript under review",
        "preprint forthcoming",
        "Gemini 3.8 Flash",
        "+3.47 points",
        "[2.47, 4.52]",
        "GPT-5.4 mini",
        "+0.98",
        "[-0.24, 2.21]",
        "Claude Sonnet 5.5",
        "+0.74",
        "[-0.23, 1.74]",
        "H1c",
        "execution floor",
        "exact test",
        "not a ranking",
        "HELM",
        "Inspect",
        "lm-evaluation-harness",
        "Invented",
        "Zorvalin",
    ):
        assert needed in research, needed
    assert "Mount Fuji" not in (ROOT / "index.html").read_text(encoding="utf-8")
    assert "tallest" not in (ROOT / "index.html").read_text(encoding="utf-8").lower()


def test_root_pages_are_keyboard_and_link_safe():
    for page_name in ROOT_PAGES:
        text = (ROOT / page_name).read_text(encoding="utf-8")
        assert 'class="skip-link"' in text, page_name
        assert 'id="main"' in text, page_name
        assert "focus-visible" in CSS
        parser = Tags()
        parser.feed(text)
        for tag, attrs in parser.tags:
            if tag != "a":
                continue
            href = attrs.get("href", "")
            if href.startswith("./"):
                path = (ROOT / unquote(urlsplit(href).path)).resolve()
                assert path.is_file(), f"{page_name} -> {href}"
            if href.startswith("https://") and attrs.get("target") == "_blank":
                rel = set(attrs.get("rel", "").split())
                assert {"noopener", "noreferrer"} <= rel, f"{page_name} {href}"
        if page_name in {"research.html", "reproducibility.html"}:
            assert "<table" in text and 'scope="col"' in text and 'scope="row"' in text, page_name


def test_citation_files_do_not_invent_a_zenodo_record():
    import json
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "cff-version: 1.2.0" in citation
    assert "version: 0.10.1" in citation
    assert "10.17605/OSF.IO/7UZV5" in citation
    assert "10.17605/OSF.IO/ANBJD" in citation
    assert "Manuscript under review" in citation
    assert "doi: 10.5281/zenodo.24193754" in citation
    assert "10.5281/zenodo.24193755" in citation
    assert "family-names: Noor" in citation and "given-names: Adeeb" in citation
    assert "https://orcid.org/0000-0002-8251-1853" in citation
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert zenodo["upload_type"] == "software"
    assert zenodo["license"] == "MIT"
    assert "doi" not in zenodo
    assert "10.5281" not in json.dumps(zenodo)


def test_small_screen_overflow_guards_are_present():
    assert ".ambient{position:fixed;" in CSS
    assert "inset:20px 0 0 0;" in CSS
    assert ".start-card{min-width:0;" in CSS
    assert ".start-grid{grid-template-columns:minmax(0,1fr);" in CSS
    assert "prefers-reduced-motion" in CSS
