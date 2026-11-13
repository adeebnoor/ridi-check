# Expert review of the RIDI Check site

Reviewer stance: a senior faculty reader of research software, asked whether https://adeebnoor.github.io/ridi-check/ would survive a lab meeting. Scores are out of 5. They describe the site as it stood after the Zenodo DOI was added and before the front-door revision in the same change set. The revision is a response to this review, not a claim that the weaknesses were never there.

Date of the reading: 13 November 2026. The manuscript is under review. A preprint is forthcoming. No journal is named.

## Rubric, before the front-door revision

| Criterion | Score | What the page actually does |
|---|---:|---|
| Clarity of the problem | 3.0 | The line “Your benchmark can stay the same. The decision may not.” is the right sentence. It is then crowded by a monitor, a ribbon, and five later sections. A new reader can leave without being able to say the risk in one breath. |
| Motivation: why use it | 2.5 | Practitioner, evaluator, and regulator are not named. The cost of a silent item-level change is one clause in the lead, not a reason to install. |
| Scientific contribution | 3.0 | The execution floor, the exact conditional test, and the comparison with HELM, Inspect, and lm-evaluation-harness exist, mostly on the science page. The home page says the tool is not proven superior before it says what it adds. |
| Rigor | 4.5 | This is the strong part. H1c is reported as not met. The exact test is labelled pending confirmation against the registered protocol. BoolQ labels are not treated as truth. No Ragas score is invented. Signed runs are linked. |
| Usability and onboarding | 2.5 | Install sits in section 05, after evidence and science. There is no sample of what `ridi-check demo` prints. The first button opens the browser tool, which is useful, and it is not a 60-second path. |
| Reproducibility | 4.0 | A reproducibility page, checksums, and signed GitHub runs are real. The home page points at them. It does not show one command and one output. |
| Credibility signals | 3.5 | OSF DOIs, the Zenodo concept DOI, and a limitations panel are present. The eyebrow “OPEN-SOURCE AI UPDATE ASSURANCE” sounds like a product claim the rest of the site carefully refuses. |
| Design | 4.0 | The dark bilingual system, focus states, and contrast are at a high standard. The information architecture is a launch page. The decision a reader must make is not the first structure. |

Mean: 3.4.

## Top weaknesses

1. The incentive is implied, not assigned. A practitioner shipping a prompt, an evaluator comparing systems, and a reviewer reading a release record are different jobs. None of them is told, in the first screen, what they would do with the output.
2. The scientific object is easy to miss. An item-level release audit with a re-execution floor is not the same object as a HELM or lm-evaluation-harness score. That sentence should be on the home page, and it should stay modest: this repository has not run those tools on the same items.
3. There is no 60-second proof. The synthetic library demo already prints four stable regressions and exits 1. That output is the fastest honest demonstration, and it was not on the home page.
4. The registered commercial result is easy to skim as a success. H1c, support in at least 2 of 3 models after Holm, was not met. Gemini 3.8 Flash was supported. GPT-5.4 mini and Claude Sonnet 5.5 were not. Those figures are the reported result. They were not recomputed here. They belonged above the fold of the science story, with the null stated first.
5. “When not to use it” is a panel of three refusals, not a path. The limitations page exists. The home page did not make that the next click for someone who might misuse a gate failure as clearance.

## What this review does not do

It does not score the manuscript. It does not treat the signed BoolQ pilots as a powered study. It does not add the either-model overlap count that was proposed as a worked example, because that count was not in the repository and was not in the public OSF files that could be read from here. The commercial figures used on the home page are the ones already reported on this site, tied to OSF DOI 10.17605/OSF.IO/ANBJD.

## After the front-door revision

The home page now names the three jobs, states the contribution against aggregate-score tools without a superiority claim, shows the synthetic demo command and its recorded gate output, and leads the commercial replication with the unmet H1c criterion. “When not to use it” links to the limitations page.

| Criterion | Before | After |
|---|---:|---:|
| Clarity of the problem | 3.0 | 4.5 |
| Motivation: why use it | 2.5 | 4.5 |
| Scientific contribution | 3.0 | 4.5 |
| Rigor | 4.5 | 4.5 |
| Usability and onboarding | 2.5 | 4.5 |
| Reproducibility | 4.0 | 4.5 |
| Credibility signals | 3.5 | 4.5 |
| Design | 4.0 | 4.5 |

Mean after: 4.5. The remaining gap is that the either-model overlap count was not added, and the exact test is still pending confirmation against the registered bootstrap. Those are limits, not unfinished sentences.
