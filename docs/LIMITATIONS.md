# Limitations

Honest limits, kept from the audits already in this repository. ridi-check finds change. It does not clear a system for use.

## Not clinical clearance

No independent clinical safety validation has been done. The invented drug-name file (`web/sample_medicines.csv`) is illustration: the names, doses, and effects are made up and are not medical guidance. A release gate that fails on those rows checks the software, not a formulary.

## Not a certificate

The release gate prints counts and can exit 1. No output says a system is fit to deploy. Passages are shown, not graded. An ungraded passage can still carry the evidence. Without an answer key, a difference is a change, not a regression.

## The execution floor is a thin baseline, and the exact test is not in the package

Two repeated runs are a thin estimate of re-execution noise. The shipped comparison asks whether the between-version change rate is strictly above both run-1 versus run-2 rates after rounding to 6 decimal places. That is not the manuscript's exact test. Details: [STATISTICS.md](STATISTICS.md).

## BoolQ labels are not ground truth

The 48-item pilots use published BoolQ labels. "Regression" there means a change against that key.

- `p0155` asks whether Hindi is India's national language. The gold label is YES. The passage says the constitution declares no national language. Dzendzik, Vogel and Foster (2020), [DOI 10.18653/v1/2020.insights-1.2](https://doi.org/10.18653/v1/2020.insights-1.2), already reported this conflict. At least one "stable regression" in the size-substitution pilot is a label problem. The raw label is kept.
- `p0315` (intercostal muscles) needs domain reading of the passage before anyone treats the gold label as anatomy.
- `p1686` asks about U.S. Air Force warrant officers. The passage predates their reintroduction in December 2024. An answer can differ for "as the passage says" and "as of 2026".
- `p0746` asks whether Flint water is drinkable "now". That question moves with time. Michigan's August 2026 announcement is about the public system and known lead service lines, not a guarantee for every building.

The flagged transitions have not been newly blinded and adjudicated. BoolQ dev is public, so training contamination is possible. These pilots are not a powered preregistered study. The same-weights McNemar p-value 0.7265625 and the BoolQ p-value of about 0.05248 were computed outside the package and are not significant at an unadjusted 0.05.

## The same seed did not fix every answer

With temperature 0 and seed 20261113, the first GitHub run of the fictional policy set matched Windows, and a later GitHub run changed baseline answers for `p03` and `p06`. BoolQ first-run answers matched across Windows and GitHub; some repeated answers did not. Reproducibility here is scoped.

## Not a ranking of other tools

This repository has not run HELM, Inspect, lm-evaluation-harness, or Ragas on the same items. The [comparison](COMPARISON.md) says what each tool is for. It does not say ridi-check is better.

## Agents, hosts, and size

Tool-using agents have a documented wrapper and a stand-in, and have not been tried on a production agent. Size was measured on Linux with Python 3.13 and Chromium, not on Windows or macOS. The measured limits are in the [reference](REFERENCE.md#measured-limits).

## Commercial replication

The preregistered criterion H1c (support in at least 2 of 3 models after Holm) was not met. The reported differences were model-dependent: Gemini 3.8 Flash was supported, and GPT-5.4 mini and Claude Sonnet 5.5 were not. Those figures are not recomputed in this repository. See the [science page](https://adeebnoor.github.io/ridi-check/research.html).
