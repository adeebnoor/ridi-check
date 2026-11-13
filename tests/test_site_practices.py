"""The public pages share navigation, citation metadata, and a local link check."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index.html", "research.html", "limitations.html", "reproducibility.html", "404.html"]


def text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_pages_share_landmarks_metadata_and_the_citation():
    for name in PAGES:
        page = text(name)
        assert 'class="skip-link"' in page, name
        assert 'id="main"' in page, name
        assert "<header" in page and "<footer" in page and "<nav" in page, name
        assert 'lang="en"' in page, name
        assert 'name="description"' in page, name
        assert 'rel="canonical"' in page, name
        assert "Content-Security-Policy" in page, name
        assert "SoftwareSourceCode" in page and "ScholarlyArticle" in page, name
        assert 'name="citation_title"' in page and 'name="citation_author"' in page, name
        assert 'name="citation_publication_date" content="2026/11/12"' in page, name
        assert "[Zenodo DOI to be added]" in page, name
        assert "No trackers" in page, name
        assert "Changelog 0.10.1" in page, name
        assert "Nature" not in page and "accepted" not in page.lower(), name
        assert "10.5281" not in page, name


def test_sitemap_and_robots_name_the_public_pages():
    robots = text("robots.txt")
    sitemap = text("sitemap.xml")
    assert "Sitemap: https://adeebnoor.github.io/ridi-check/sitemap.xml" in robots
    for loc in (
        "https://adeebnoor.github.io/ridi-check/",
        "https://adeebnoor.github.io/ridi-check/research.html",
        "https://adeebnoor.github.io/ridi-check/limitations.html",
        "https://adeebnoor.github.io/ridi-check/reproducibility.html",
        "https://adeebnoor.github.io/ridi-check/web/ridi-update-check.html",
    ):
        assert loc in sitemap


def test_local_link_checker_passes():
    done = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_links.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert done.returncode == 0, done.stderr
    assert os.path.isfile(ROOT / "tools" / "check_links.py")
