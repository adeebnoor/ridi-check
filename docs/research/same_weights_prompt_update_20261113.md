# Same-weights Qwen prompt update: completed exploratory evidence

**State:** Windows and GitHub CPU runs complete; published BoolQ labels are not a newly adjudicated standard. **Not a clinical safety result, model-weight revision, naturally occurring update, or benchmark-framework superiority claim.**

## Controlled intervention

- The *same*, checksum-pinned `Qwen2.5-1.5B-Instruct-Q4_K_M` GGUF weights were loaded **once** and used for both 'current' and 'proposed' answers. It was a system-instruction update only: current prompts the model to use **only the supplied passage**; proposed allows a **general-knowledge fallback** if the passage seems incomplete/inaccurate. This is a meaningful configuration/update contrast, not an update of the model's own learned parameters.
- Frozen sample: seeded 48 questions (24 YES/24 NO) from public BoolQ dev with exact same passage per arm, 3 runs per model arm (288 actual calls), `temperature=0`, `seed=20261113`, same endpoint, CPU llama.cpp release `b12327`. Frozen source: `experiments/same_weights_prompt/PRE_RUN_FROZEN.json`. Source-generated `questions.csv` SHA-256: `3fa33a0e7e968c99056ffe17a430a555a9678f717d6fdcc78e1c352dfa4eb462`.
- Two independent execution environments: authorized Windows desktop and GitHub Actions `ubuntu-24.04` runner. GitHub run [43317397792](https://github.com/adeebnoor/ridi-check/actions/runs/43317397792) completed successfully, executed **288/288 calls**, verified `results.csv` against raw outputs and hashes, created GitHub Actions/Sigstore provenance for `evidence.json` and independently verified its attestation. GitHub evidence SHA-256: `cf5359da1222170064d95905470aa163b107f4ee55f4c2405a67e23598ffe64e`. Source artifact: [GitHub workflow](https://github.com/adeebnoor/ridi-check/actions/runs/43317397792).

## Findings

| Measure | Windows | GitHub Ubuntu |
|---|---:|---:|
| Completed model calls | 288/288 | 288/288 |
| Correct against **published** BoolQ labels, current | 35/48 | 34/48 |
| Correct against **published** BoolQ labels, proposed | 33/48 | 32/48 |
| First-run gains / regressions | 3 / 5 | 3 / 5 |
| Stable regressions across 3 repeats | 5 | 4 |
| Stable improvements across 3 repeats | 3 | 2 |
| Within-run unstable cases | 0 | 3 |
| Answers different on first run | 8/48 | 8/48 |
| Strict `--check-scores` release gate | rejects | rejects |

- Stable regression IDs Windows: `p0746,p1506,p1686,p2179,p2735`; GitHub: `p1506,p1574,p2179,p2735`. Stable improvement IDs Windows: `p0163,p0603,p1192`; GitHub: `p0163,p1192`. GitHub unstable IDs: `p0358,p0746,p1686`. Thus **cross-platform case-level stability is not fully invariant**, even with pinned weights and deterministic decoding flags.
- First-run McNemar exact two-sided p-value (3 gains vs 5 losses): **0.7265625**, *not* statistically significant at 0.05. The 48-case stratified sample is not representative, and this exploratory design was not a preregistered powered study of improvement or deterioration.
- Identical passages are **input-evidence identity**, not evidence of a metric such as nDCG@10 being unchanged; there was no retrieval/ranking experiment or qrels in this prompt-update pilot.
- Three-rerun states improve interpretation over a **single-run** comparison but do not prove true deterministic stability; inference environment itself deserves controlled factorial treatment.

## Minimum honest baselines

1. **Aggregate accuracy only** reports net -2 correct (Windows and GitHub), but hides which individual decisions became wrong.
2. **Per-case correctness difference** (a basic pre-existing technique, not uniquely RIDI) detects all 5 first-run regressions and 3 gains from published tags. RIDI must not claim exclusive ability to detect them.
3. **Single-run literal answer difference** detects 8 first-run changes, but cannot distinguish repeat instability.
4. **RIDI** reconstructs evidence-backed per-case states with repeats, differentiates stability and instability, checks score consistency and blocks an unacceptable release; claims of superiority to HELM/Ragas/Inspect AI require separate task-equivalent tests of those frameworks, **not this baseline table**.

## Historical-ground-truth problems and novelty guardrails

- **Published prior art:** Dzendzik, Vogel & Foster (2020) introduced 'stable accuracy' and discussed model run variability, BoolQ noise and even the **identical** Hindi-national-language label contradiction (case `p0155` here). See [ACL Anthology / DOI 10.18653/v1/2020.insights-1.2](https://aclanthology.org/2020.insights-1.2/). Do **not** represent these as novel RIDI discoveries.
- **Time-dependent labels:** `p1686` concerns USAF warrant officers; they were reintroduced in late 2024 ([US Air Force, 2025](https://www.104fw.ang.af.mil/News/Article-Display/Article/4201227/washington-air-guards-warrant-officers-pave-way/)). `p0746` asks if Flint drinking water is safe *now*; [Michigan, August 2026](https://www.michigan.gov/whitmer/news/press-releases/2026/08/13/icymi-whitmer-mayor-sheldon-mark-milestone-completed-lead-service-line-replacement-in-flint) reports 10 years of public-system compliance and replacement of known lead service lines. Water quality can still vary by building. These cases must be adjudicated separately as-of-passage and as-of-2026. A wrong score against an old BoolQ label is **not** proof of a worse real-world decision.
- **Potential model-train contamination:** BoolQ dev is public. No independent blinded RIDI transition grading has been performed; the human-review packet has blank rater cells only.

## Next scientific gates

- Have **two independent blind raters** assess the flagged states and selected stable controls for passage-supported vs current-world truth, label conflict, material action difference and uncertainty; preserve raw gold vs adjudicated gold scores; calculate agreement and resolve discrepancies transparently.
- Extend beyond YES/NO to answers with **equal benchmark scores but materially different wording/actions**; this binary BoolQ comparison alone cannot test the paper's full claim.
- Run a *controlled backend × seed × batch* factorial and a naturally occurring retrieval-score equivalent contrast, not merely prompt instructions, with sample size, multiple-model replication, frozen protocol and uncertainty intervals.
- Compare actual pipelines using HELM/Inspect/Ragas as appropriate, on matched tasks and report tool/runtime overhead; no invented framework scores.
