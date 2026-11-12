# Scientific and engineering audit: RIDI Qwen and BoolQ pilots

> **Scope:** Exploratory engineering reproduction on real open-weight language models, NOT clinical validation, NOT an independent blind human audit, NOT an RAG retrieval equivalence experiment, and NOT a head-to-head victory against other frameworks.

## Design and provenance

- Original Windows CPU run: Qwen2.5-0.5B-Instruct Q4_K_M (`current`) vs Qwen2.5-1.5B-Instruct Q4_K_M (`proposed`), llama.cpp `b12327`, localhost only; temperature=0, seed=20261113; two attempts per question/model.
- The two models have **different parameter counts**. This tests model substitution, not revisions of an identical model.
- 24 constructed fictional library-policy questions are **not** externally labeled; BoolQ validation contains published human-provided binary labels, with an intentionally stratified random 24 YES / 24 NO sample (N=48) frozen before inference. All compared source passages are identical within each case.
- Frozen inputs and model SHA-256 values are in `PRE_RUN_FROZEN.json`, with reconstruction code in `boolq_builder.py`. Checksums are verified in the CI workflow.
- Two distinct GitHub Actions workflows independently executed these computations, signed `evidence.json` using Sigstore/Rekor identity and verified the signatures: [Qwen first GitHub run](https://github.com/adeebnoor/ridi-check/actions/runs/43311544032), [Qwen repeat and BoolQ GitHub run](https://github.com/adeebnoor/ridi-check/actions/runs/43312668253).

## Observed outcomes (not estimates of clinical harm)

| Dataset/host | Requests | Accuracy current → proposed | Stable regressions | Stable improvements | Within-run unstable |
|---|---:|---:|---:|---:|---:|
| Fictional policies / Windows CPU | 96/96 | 20/24 → 21/24 | 3 | 4 | 0 |
| Fictional policies / first GitHub Linux CPU | 96/96 | 20/24 → 21/24 | 3 | 4 | 0 |
| Fictional policies / second GitHub Linux CPU | 96/96 | 20/24 → 21/24 | 3 | 4 | 0 |
| BoolQ / Windows CPU | 192/192 | 26/48 → 36/48 | 6 | 16 | 2 |
| BoolQ / GitHub Linux CPU | 192/192 | 26/48 → 36/48 | 6 | 16 | 0 |

- Fictional-policy stable regression IDs across all three runs: `p10, p16, p22`. In the **first** Windows/GitHub comparison, the stable improvement IDs were `p02, p03, p15, p21`; on a **second** GitHub run they were `p02, p06, p15, p21` because the **0.5B baseline responses** for p03/p06 changed between runs. Aggregate counts did not change.
- The fictional-policy first GitHub `results.csv` had the **same SHA-256** as Windows (`d547eb657994a5e751fa466a22eacb5ba38a6067c81263eebc426f11f251b728`); the second GitHub `results.csv` did **not**. Consequently exact reproducibility cannot be claimed for arbitrary repeated CI jobs.
- BoolQ first-run model answers were **byte-identical** across Windows and GitHub when serialized in ordered JSON (SHA-256 `9bfc81a0b178da149436a908e097e9e2e3bfc69803e45a8774567e456b9a195f`). The six regression IDs are `p0155,p0163,p0315,p1192,p3057,p3078`, and the same 16 improvement IDs were recovered. In Windows Qwen1.5 had repeat-level answer changes for cases `p0358,p0603`; GitHub did not. Full multi-repeat results therefore differ.
- For the 48 stratified BoolQ cases, a two-sided exact paired McNemar/binomial test for 16 improved versus 6 worsened first-run correct/incorrect decisions gives **p≈0.05248**. This is not significant at an unadjusted 0.05 threshold. No justified inference to a broader real-world distribution follows from this selected public subset.

## Gold-label contradictions and adjudication required (P0)

- **Case p0155:** BoolQ gold answer is `YES` for the question *'is hindi is our national language of india'*. But the supplied passage explicitly says **'There is no national language as declared by the Constitution of India.'** The 0.5B `YES` was scored correct, and the 1.5B `NO` was scored as a stable regression, although `NO` agrees with this specific passage. **Therefore at least one of the six 'regressions' is a questionable benchmark-label finding, not an independently demonstrated semantic error.** Do not auto-relable or silently delete it; submit for blinded adjudication and retain original and adjudicated scoring separately.
- **Case p0315:** The published BoolQ gold is `YES` for internal intercostal contraction during inspiration, but the passage supplied discusses assistance in exhalation; its interpretation needs domain-expert adjudication, not an automatic label reversal.
- Both issues illustrate why aggregate accuracy and a public gold answer do not substitute for expert review of question/evidence/expected answer.

## Comparator baseline and limitations

- **Aggregate accuracy-only baseline** on BoolQ yields +10 correct (26→36) and does not reveal the **six** per-case regressions. A conventional **per-case label transition** analysis *does* detect those six; RIDI's additional engineering contribution is its explicit re-run states, changed-answer visibility, evidence provenance and release gate. Do not claim existing research frameworks cannot perform per-case comparisons.
- Answers are strictly YES/NO; this dataset does not test nuanced multi-class decisions, answer semantics, error severity, relevance grades, retrieval chunking causal effects, or the 1,131 constructed semantic-transition rules.
- Comparing the two models under this deterministic prompt and quantization does not estimate the frequency of model-update errors in deployed systems.
- Model training data may include public BoolQ dev examples (possible contamination). Human gold labels were created by dataset authors but independent blinded adjudication of RIDI's flagged transitions **has not occurred**.
- GitHub attestations authenticate the workflow-produced files and their checksums. They do **not** certify the truth of labels, correctness of models, completeness of attempted experiments, or clinical safety.

## Publication/release decision

**Engineering proof of execution and reproducibility: YES, scoped.**
**Scientific head-to-head superiority: NOT TESTED.**
**Independent decision-level gold adjudication: OPEN.**
**Clinical or high-stakes deployment clearance: NO.**

Recommended next controlled studies: (1) blinded adjudication of each regression/gain and a stratified sample of stable cases, explicitly including p0155/p0315; (2) real same-model update/change experiment; (3) a preselected naturally distributed holdout with repeated runs and uncertainty; (4) fair task-matched comparison using HELM/Inspect/Ragas-compatible evaluation pipelines.
