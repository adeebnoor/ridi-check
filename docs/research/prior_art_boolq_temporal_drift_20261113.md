# RIDI research guardrails: prior art, gold-label noise and temporal drift

**Review date:** 2026-11-13. This note limits claims; it does not revise frozen inputs or official BoolQ labels.

## Important prior art

Daria Dzendzik, Carl Vogel and Jennifer Foster (2020), *Q. Can Knowledge Graphs be used to Answer Boolean Questions? A. It's complicated!*, [ACL Anthology, DOI 10.18653/v1/2020.insights-1.2](https://aclanthology.org/2020.insights-1.2/), examined model re-run variability and defined **stable accuracy**. Their error audit identified a specific BoolQ gold-label contradiction: the Hindi-national-language question asks if Hindi is India's national language, while its passage says the constitution declares **no national language**; the original gold tag YES conflicts with that passage. This is the same `p0155` case in our 48-case pilot. The paper reported approximately **6% label mistakes among 200 inspected baseline errors**, not 6% of BoolQ as a whole.

RIDI therefore must **not** claim that 'stable accuracy' or basic answer inconsistency was previously unknown, nor claim RIDI was first to identify this BoolQ issue. A defensible novel contribution, if comparative experiments support it, would combine frozen update contrasts, case-level change categories, evidence hashes and attestations, and a falsifiable CI release gate.

## Temporal/context confounds in the 48-case BoolQ sample

- `p1686` asks whether the U.S. Air Force has warrant officers. The old BoolQ passage says it did not; the Air Force reintroduced the ranks in December 2024, corroborated in [an official Air Force report, May 2025](https://www.104fw.ang.af.mil/News/Article-Display/Article/4201227/washington-air-guards-warrant-officers-pave-way/). An answer can differ depending on whether the task is 'according to historical passage' or 'as of 2026'.
- `p0746` asks whether Flint water is drinkable 'now'. This is inherently time-sensitive; [Michigan's August 2026 announcement](https://www.michigan.gov/whitmer/news/press-releases/2026/08/13/icymi-whitmer-mayor-sheldon-mark-milestone-completed-lead-service-line-replacement-in-flint) says the public water system has met lead standards and all known lead service lines were replaced. This does not guarantee every household's water quality. Do not treat a decades-old categorical answer as a time-invariant clinical or public-health ground truth.
- `p0155` is confirmed as a documented known dataset-label problem by Dzendzik et al. (2020). Retain the raw label and introduce a separately adjudicated correction, never rewrite the original dataset silently.

## Independent blinded adjudication protocol

Before publication, independently ask two human raters to assess: the most supportable answer from the **given passage**; the answer **at a clearly specified current date** where appropriate; evidence sufficiency; label noise; and whether there is a materially different action. Hide model identity, arm order, original gold tags and RIDI transition classes from reviewers. Include changed cases and a prespecified sample of unchanged controls. Resolve disagreements by recorded adjudication, report inter-rater agreement and corrected results separately from original benchmark results. Preserve the original labels and all fingerprints.

## What current experiments do and do not show

Real Qwen local+GitHub runs establish technical feasibility and scoped reproducibility; BoolQ 48 labels are provided by third parties but the **RIDI-flagged transitions have not been newly blinded/adjudicated**. A same-weight prompt-configuration update tests the effect of source-authority instructions, **not a model-weight update**. None of these outcomes establishes clinical harm, global superiority over HELM/Inspect/Ragas, or natural prevalence of meaningful decision changes.
