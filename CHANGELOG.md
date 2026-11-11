# Changelog

Notable changes to ridi-check. Versions follow [semantic versioning](https://semver.org/); before 1.0 the
library API may change between minor versions.

## 0.3.2

### Added
- A release workflow that publishes to PyPI through Trusted Publishing when a GitHub Release is published.
- `index.html` at the repository root, so that a hosted copy of the browser version has a short address.
- Adapter examples in `examples/adapters`: an OpenAI-compatible HTTP API, the Claude API through its
  official SDK, and a shell command. Each is tested against a local stand-in server.
- `docs/REFERENCE.md`: every command and option, the settings and questions files, `results.csv`, the
  labelling rules and exit status.
- `CONTRIBUTING.md`, `SECURITY.md`, issue forms and a pull request template.

### Changed
- The README is a front page, with a real screenshot of the demo report and the reference moved out.
- The browser version in `web/` uses the reader's own fonts and makes no network request.

### Fixed
- The address of an http system may come from the environment (`${BASE_URL}/path`).

## 0.3.1

First public release.

- `ridi-check run`, `report` and `gate`; `demo` and `init` for a first use.
- Python, command and http adapters; resumable runs that record every attempt.
- One self-contained HTML report in English and Arabic, a JSON summary and the cases to review as CSV.
- A browser version in `web/`, checked against the Python on random files.
- User guide, use cases and developer guide in English and Arabic.
- Tested on Linux, macOS and Windows with Python 3.10 and 3.13.
