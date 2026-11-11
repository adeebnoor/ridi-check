"""The README and the guides: every link into this repository must lead somewhere."""

import os
import re

import pytest

from conftest import ROOT

REPO = "https://github.com/adeebnoor/ridi-check"
RAW = "https://raw.githubusercontent.com/adeebnoor/ridi-check/main/"
PAGES = ["README.md"] + sorted(os.path.join("docs", name) for name in os.listdir(os.path.join(ROOT, "docs"))
                               if name.endswith(".md"))
LINK = re.compile(r"\]\(([^)\s]+)\)")


def read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as f:
        return f.read()


def slugs(text):
    """Heading anchors the way GitHub makes them."""
    out = set()
    for heading in re.findall(r"^#{1,6} +(.+?)\s*$", re.sub(r"```.*?```", "", text, flags=re.S), re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.strip().lower(), flags=re.UNICODE).replace(" ", "-")
        out.add(slug)
    return out


@pytest.mark.parametrize("page", PAGES)
def test_links_into_the_repository_resolve(page):
    text = read(page)
    checked = 0
    for target in LINK.findall(text):
        anchor = None
        if target.startswith("#"):
            path, anchor = page, target[1:]
        elif target.startswith(RAW):
            path = target[len(RAW):]
        elif target.startswith(REPO + "/blob/main/"):
            path, _, anchor = target[len(REPO + "/blob/main/"):].partition("#")
        elif target.startswith(("http://", "https://")):
            continue                                    # another site, or a page GitHub generates (issues, actions)
        else:
            relative, _, anchor = target.partition("#")
            path = os.path.normpath(os.path.join(os.path.dirname(page), relative))
        assert os.path.exists(os.path.join(ROOT, path)), f"{page}: {target} points at a file that does not exist"
        if anchor and path.endswith(".md"):
            assert anchor in slugs(read(path)), f"{page}: {target} points at a heading that does not exist"
        checked += 1
    assert checked or page != "README.md"


def test_readme_is_a_front_page():
    text = read("README.md")
    order = ["## What you will see", "## Who it is for", "## Start in one minute", "## Use it in CI",
             "## Connect your assistant", "## FAQ", "## Roadmap", "## Limitations", "## Licence"]
    positions = [text.index(heading) for heading in order]
    assert positions == sorted(positions)
    assert "docs/img/report.png" in text and "actions/workflows/tests.yml/badge.svg" in text
    assert "It finds change, not correctness." in text and "It is not a readiness or safety certificate." in text
    assert not re.search(r"img\.shields\.io|badgen\.net", text)          # badges are served from this repository
    for name in ("report.png", "report-case.png", "badge-licence.svg", "badge-python.svg"):
        assert os.path.getsize(os.path.join(ROOT, "docs", "img", name)) > 200
