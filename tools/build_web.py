"""Build the browser version: web/ridi-update-check.html, one file that works without a server.

    python tools/build_web.py                 # writes web/ridi-update-check.html
    python tools/build_web.py --fragment F    # also writes the page without its document skeleton

The page is assembled from web/template.html, web/core.js (the analysis), web/app.js (the page),
the report stylesheet in src/ridi_check/report_template.html, web/extra.css, the report strings in
src/ridi_check/strings.py and web/sample_results.csv. tests/test_web.py fails when the built file
is out of date.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ridi_check import __version__  # noqa: E402
from ridi_check.strings import strings_for  # noqa: E402

OUTPUT = os.path.join(ROOT, "web", "ridi-update-check.html")


def read(*parts: str) -> str:
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def embed(value: object) -> str:
    """JSON that is safe inside a <script> block."""
    blob = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return blob.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


FONT_LINK = re.compile(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^"]*">\n')


def build(web_fonts: bool = False) -> str:
    """The page. Without `web_fonts` it loads nothing from anywhere and uses the reader's own fonts."""
    report = read("src", "ridi_check", "report_template.html")
    style = re.search(r"<style>\n(.*?)</style>", report, re.S).group(1)
    page = read("web", "template.html")
    parts = {
        "__STYLE__": style.rstrip("\n") + "\n" + read("web", "extra.css").rstrip("\n"),
        "__STRINGS__": embed({"key": strings_for("key"), "nokey": strings_for("nokey")}),
        "__SAMPLE__": embed(read("web", "sample_results.csv")),
        "__CORE__": read("web", "core.js").rstrip("\n"),
        "__APP__": read("web", "app.js").rstrip("\n"),
        "__VERSION__": __version__,
    }
    for name, value in parts.items():
        assert page.count(name) == 1, name
        page = page.replace(name, value)
    assert len(FONT_LINK.findall(page)) == 1
    return page if web_fonts else FONT_LINK.sub("", page)


def fragment(page: str) -> str:
    """The parts between the page markers: what a host that supplies its own skeleton needs."""
    return "\n".join(m.group(1).strip("\n") for m in re.finditer(r"<!--page-->(.*?)<!--/page-->", page, re.S)) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fragment", metavar="FILE", help="for a host that allows web fonts; this copy loads them")
    args = parser.parse_args()
    page = build()
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"wrote {OUTPUT} ({len(page.encode('utf-8')) // 1024} KB)")
    if args.fragment:
        with open(args.fragment, "w", encoding="utf-8", newline="\n") as f:
            f.write(fragment(build(web_fonts=True)))
        print(f"wrote {args.fragment}")


if __name__ == "__main__":
    main()
