# RIDI Check product-spec audit and implementation — 13 November 2026

**Reference reviewed:** user-supplied `ridi_silicon_valley_master_spec_v011.md` (proposed version 0.11.0). **Code branch:** `site/deep-linked-auditable-demos-20261113`, based on latest upstream main `0ac3f2e` (which already incorporated additional independent research/site enhancements).

**Important:** This work upgrades the **product website and live browser inspector** without silently changing the published Python package. The package's recorded version remains **0.10.1** until an intentional, verified tagged release. Do not represent an unreleased `0.11.0` as available on PyPI or Zenodo.

## Review of all eight specification points

| # | Diagnosis / request | Verified code reality | Action |
|---|---|---|---|
| 1 | Home evidence cards link to external CI rather than the interactive inspector | The real runs were on GitHub only; homepage lacked case-level deep links | **Implemented.** Each card now opens a meaningful live inspector preset: Qwen prompt update, Qwen model swap, or the **correctly labelled synthetic** library demo. Original signed-run and scientific-audit links are preserved. |
| 2 | Real clinical DDI, BoolQ and counterfactual data should all be in the demo | Authentic, externally adjudicated clinical DDI cases and a validated pharmacovigilance ground truth are **not present** | **Partially implemented, science-safe.** Added two **real signed Qwen/BoolQ** CSVs, 48 cases each, SHA-256 matched to GitHub Actions artifacts. Kept fictional medicines explicitly fictional. The clinical/medical preset fails closed with an explanatory message; no fabricated benchmark or cases. |
| 3 | Broken header glyphs | Browser tool already had an inline SVG product logo; no icon-font dependency was verified | **Implemented real navigation** instead of replacing the working SVG. Added clear Overview, Research, GitHub and privacy labels; avoided unsupported icon-font characters. |
| 4 | One-click copy for CLI and BibTeX | Landing already had working CLI copy handler | **Implemented BibTeX copy** using that proven handler. DOI and title use real Zenodo/DataCite software metadata, not invented version or publication details. |
| 5 | Copyable GitHub Actions release gate | CLI only supports `demo`, `init`, `run`, `report`, `verify`, `gate`; no `compare` subcommand | **Implemented correct YAML** and a copy button. The file is under `examples/ci/`, not `.github/workflows/`, to avoid accidentally running an unconfigured sample workflow inside RIDI's own repository. |
| 6 | Multi-run stability omitted, wrong-to-wrong answer drift ignored | `web/core.js` **already** uses `every((r) => eq(r, first))` on both arms and records `answerChange` on `wrong_both`, including stable/varied. The first-to-second-run rate is separately reported as the execution floor, not the total-run classifier. | **Preserved existing correct, cross-tested algorithm**; added source regression tests rather than rewriting working classification logic. A zero correct-score difference does not imply identical text. |
| 7 | Tool dead end without a footer or back navigation | Tool had a small footnote but no practical navigation to the full research site | **Implemented** accessible Overview / Research links and a distinct footer linking Zenodo, ORCID and the reproducibility page. |
| 8 | Developer name as “Professor NooR”, no academic links | The main page indeed contained legacy `Professor NooR` text and metadata | **Corrected** to “Prof. Adeeb Noor” in display, “Adeeb Noor” in scholarly metadata and JSON-LD, plus verified official site, publications dashboard, ORCID and Google Scholar links. Recomputed JSON-LD CSP SHA-256. |

## Scientific, licensing and technical boundaries

1. The source datasets are the **original signed GitHub Actions `results.csv` bytes**; the browser SHA-256 checks must match exactly:
   - same-weights prompt: `18286273cf15a062629eaa59a3dbe976ea658a72d82d2b1dad5248e9b2e8317d`, [signed run](https://github.com/adeebnoor/ridi-check/actions/runs/43317397792)
   - Qwen model swap: `8d9d0b48b48a0802df239fb47bbfa2dc9a72cb3eece853514aefec9ad982c629`, [signed run](https://github.com/adeebnoor/ridi-check/actions/runs/43312668253).
2. Original BoolQ labels may be wrong or time-dependent (published literature documented the Hindi national-language discrepancy); a published-label regression is **not by itself a demonstrated harm**. Both presets are explicitly nonclinical.
3. BoolQ question/passage content is third-party **CC BY-SA 3.0**; see [preset attribution](../web/presets/README.md). Only that data is subject to its original terms; RIDI program source remains MIT.
4. Public presets use **bounded, same-origin, SHA-256-checked GET** requests on user selection or allowlisted deep links; no user's uploaded CSV is transmitted. The *existing synthetic demonstrations* still work as a standalone offline HTML.
5. GitHub Actions gate assumes an actual `ridi-check.json` plus adapter and a valid reference key/scorer; strict gating is not a clinical clearance certificate.
6. No head-to-head scientific superiority against MIT/Stanford's tools is claimed or demonstrated. That requires task-matched, independent comparisons.

## Release standard

Code generation source-of-truth remains `web/template.html`, `web/extra.css`, `web/app.js` and `web/core.js`; the built `web/ridi-update-check.html` is committed only after regeneration via `python tools/build_web.py`. Run `pytest`, reproduce the two signed sources, inspect the real browser navigation, test Arabic RTL and mobile, confirm tampered preset SHA-256 rejection, and verify that a user's CSV is not POSTed. Only merge and deploy after all checks pass.
