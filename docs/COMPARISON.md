# Comparison with other evaluation tools

This table says what each project is for. It is not a leaderboard. This repository has not run the other tools on the same items, and it does not report scores for them. ridi-check is not claimed to be better.

What ridi-check adds, as a report rather than a rank: item-level answer transitions on matched items, set next to a re-execution floor from repeated runs, plus a release gate that can fail a build. That gate is an application of the item labels. Sample logs in other tools can also show single answers. This table does not say they cannot.

| | What it is | Usual reported unit | Repeated runs | Item-level transitions beyond a re-execution floor |
|---|---|---|---|---|
| [HELM](https://crfm.stanford.edu/helm/) (Stanford CRFM) | Holistic Evaluation of Language Models: scenarios, metrics, and public leaderboards | Scenario-level metrics | Possible for a scenario; not the object of an update certificate | Not what HELM publishes. Not run here. |
| [Inspect](https://inspect.aisi.org.uk/) (UK AI Security Institute) | A framework for configuring, logging, and scoring model and agent evaluations | Task scores, samples, and logs | The run can be repeated; that is configuration | Not what Inspect publishes as an execution-floor test. Not run here. |
| [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) (EleutherAI) | A harness for standard language-model benchmarks | Task scores, with per-sample outputs available | Depends on the task configuration | Not the harness's usual certificate. Not run here. |
| ridi-check (this repository) | Compares two versions of one system on matched items | Per-item transition, plus the descriptive execution floor | Part of the method: run 1 against run 2 is the floor | Yes, as a comparison of rounded rates. The manuscript's exact test is not computed. The release gate can fail a build. |

[Ragas](https://docs.ragas.io/) is a library of retrieval-augmented generation metrics. It is named because earlier notes promised not to invent a comparison with it. No Ragas score is reported here.

Read [STATISTICS.md](STATISTICS.md) before describing the floor as an exact test, and [LIMITATIONS.md](LIMITATIONS.md) before describing a gate failure as clearance.
