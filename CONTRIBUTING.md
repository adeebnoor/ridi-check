# Contributing to ridi-check

Thank you for helping. Small, focused changes are the easiest to review and merge.

## Set up

```bash
pip install -e ".[test]"
```

```bash
pytest
```

Python 3.10 or later. The tests need no network and no API key. Two groups run only when their tool is
present: the browser-version parity tests need Node.js, and the Claude adapter example needs
`pip install anthropic`. CI runs everything on Linux, macOS and Windows.

## Ground rules

- **One place for the rules.** A new case state or rate goes in `src/ridi_check/analysis.py` with a test,
  and in `web/core.js`. The parity test fails until both agree. The report page computes nothing.
- **Two languages.** Text shown to people lives in `src/ridi_check/strings.py`, in English and Arabic.
- **Careful wording.** Without an answer key or a judgment, a difference is a "change", never a
  "regression". Nothing the tool prints may say or imply that a system is safe, certified or ready.
  `tests/test_report_gate.py` checks this.
- **Synthetic data only.** Examples, fixtures and screenshots must not contain real user data, real model
  transcripts or benchmark text.
- **No secrets.** Keys are read from environment variables. Never commit one, and never paste one into an
  issue or a pull request.
- **No new runtime dependencies** without discussing it in an issue first. The tool installs with none.
- After changing anything under `web/` or the report stylesheet, run `python tools/build_web.py`.

## Proposing a change

1. For anything larger than a fix, open an issue first and describe the problem you want solved.
2. Add or update a test that fails without your change.
3. Run `pytest`. Update the docs and `CHANGELOG.md` when behaviour changes.
4. Open a pull request and fill in the template.

## Reporting a bug

Use the bug report form. The most useful report has the command you ran, what you expected, what
happened, and the smallest `results.csv` that shows it, with synthetic content.

## Security

Do not open a public issue for a vulnerability. See [SECURITY.md](SECURITY.md).

## Licence

By contributing you agree that your contribution is licensed under the [MIT licence](LICENSE).
