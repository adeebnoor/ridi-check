"""The README and the guides: every link into this repository must lead somewhere."""

import os
import re

import pytest

from conftest import ROOT

REPO = "https://github.com/adeebnoor/ridi-check"
RAW = "https://raw.githubusercontent.com/adeebnoor/ridi-check/main/"
PAGES = (["README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md", os.path.join("examples", "README.md"),
          os.path.join("examples", "adapters", "README.md"), os.path.join("tests", "fixtures", "README.md")]
         + sorted(os.path.join("docs", name) for name in os.listdir(os.path.join(ROOT, "docs")) if name.endswith(".md")))
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
             "## Connect your assistant", "## FAQ", "## Roadmap", "## Limitations", "## Contributing", "## Licence"]
    positions = [text.index(heading) for heading in order]
    assert positions == sorted(positions)
    assert "docs/img/report.png" in text and "actions/workflows/tests.yml/badge.svg" in text
    assert "It finds change, not correctness." in text and "It is not a readiness or safety certificate." in text
    assert not re.search(r"img\.shields\.io|badgen\.net", text)          # badges are served from this repository
    for name in ("report.png", "report-case.png", "badge-licence.svg", "badge-python.svg"):
        assert os.path.getsize(os.path.join(ROOT, "docs", "img", name)) > 200


def test_no_file_holds_an_email_address():
    """Contact goes through GitHub: issues, and private vulnerability reports. No mailbox is published."""
    address = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist", "out", "node_modules"}
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.endswith(".egg-info") and not d.startswith("ridi-")]
        for name in files:
            path = os.path.join(folder, name)
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                continue                                   # images and other binary files
            found += [f"{os.path.relpath(path, ROOT)}: {m}" for m in address.findall(text)]
    assert not found, found


def test_community_files_are_in_place():
    for name in ("CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md", "LICENSE", os.path.join(".github", "pull_request_template.md"),
                 os.path.join(".github", "ISSUE_TEMPLATE", "bug_report.yml"),
                 os.path.join(".github", "ISSUE_TEMPLATE", "feature_request.yml"),
                 os.path.join(".github", "ISSUE_TEMPLATE", "config.yml")):
        assert os.path.getsize(os.path.join(ROOT, name)) > 100, name
    security = read("SECURITY.md")
    assert "Report a vulnerability" in security and "no email address" in security
    conduct = read("CODE_OF_CONDUCT.md")
    assert "Contributor Covenant, version 2.1" in conduct and "Report a vulnerability" in conduct
    assert "no email address" in conduct
    assert "CODE_OF_CONDUCT.md" in read("CONTRIBUTING.md") and "CODE_OF_CONDUCT.md" in read("README.md")


def test_root_page_leads_to_the_browser_version():
    page = read("index.html")
    target = re.search(r'http-equiv="refresh" content="0; url=([^"]+)"', page).group(1)
    assert target == "web/ridi-update-check.html" and os.path.exists(os.path.join(ROOT, target))
    assert f'href="{target}"' in page                      # a plain link too, for readers without script or refresh
    assert os.path.exists(os.path.join(ROOT, ".nojekyll"))  # the files are served as they are


def test_release_workflow_publishes_without_any_stored_secret():
    workflow = read(os.path.join(".github", "workflows", "release.yml"))
    for needed in ("types: [published]", "python -m build", "twine check", "id-token: write", "name: pypi",
                   "pypa/gh-action-pypi-publish@release/v1"):
        assert needed in workflow, needed
    assert workflow.index("twine check") < workflow.index("pypa/gh-action-pypi-publish")
    assert not re.search(r"secrets\.|password:|PYPI_API_TOKEN|TWINE_PASSWORD|TWINE_USERNAME", workflow)
    assert "push:" not in workflow and "pull_request" not in workflow     # a published Release is the only trigger


def test_package_metadata():
    text = read("pyproject.toml")
    for needed in ('license = "MIT"', 'readme = "README.md"', "[project.urls]", "Homepage", "Changelog", "Issues",
                   '"regression-testing"', "Programming Language :: Python :: 3.10", "Topic :: Software Development :: Testing"):
        assert needed in text, needed
    assert "License ::" not in text                         # the licence is given once, as an SPDX expression
    assert 'authors = [{ name = "ridi-check contributors" }]' in text and "email" not in text
    version = re.search(r'__version__ = "([^"]+)"', read(os.path.join("src", "ridi_check", "__init__.py"))).group(1)
    assert f"## {version}" in read("CHANGELOG.md"), "the changelog has no section for the current version"


def test_the_size_figures_on_the_front_page_are_the_measured_ones():
    """The README is the PyPI page: its figures must be the ones in the reference, with their caveat."""
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        readme = f.read()
    with open(os.path.join(ROOT, "docs", "REFERENCE.md"), encoding="utf-8") as f:
        reference = f.read()
    for figure in ("552 MB", "17.9 MB", "100,000 cases"):
        assert figure in readme and figure in reference, figure
    assert "not on Windows or macOS and not in the browser" in " ".join(readme.split())

