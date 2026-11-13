# The execution floor and the exact test

This note says what ridi-check computes, and what the manuscript describes that this package does not compute. The arithmetic in the package was not changed to resemble a test it does not run.

## Terms

- **Matched items.** The same `case_id` is run on the current version and the proposed version. Rows are not paired by similarity after the fact.
- **Repeated runs.** Each version may be run more than once. The label "stable" requires every run of a version to agree with that version's first run, and at least two runs of both versions. Otherwise the item is `unstable`, or `unconfirmed` when a version was run once.
- **Execution floor.** The re-execution noise baseline: how often a version disagrees with itself. In this package that is the run-1 versus run-2 disagreement rate of each version. The floor rate is the larger of those two rates.
- **Exact test.** The manuscript under review describes an exact test of whether answer changes go beyond that floor. **ridi-check does not compute it.** `summary.json` sets `execution_floor.exact_test_implemented` to `false` and has no p-value.

The **release gate** is an application of the item labels (for example a limit on stable regressions). It does not read the floor comparison and it does not certify a system.

## What `report` calculates

For every compared item, `analyse` counts:

| Count | Definition |
|---|---|
| Change between versions | First run of the current version differs from the first run of the proposed version |
| Re-run, current | Run 1 differs from run 2 of the current version |
| Re-run, proposed | Run 1 differs from run 2 of the proposed version |

Each rate is `round(count / n, 6)`. The Wilson 95% interval uses the constant `z = 1.959964` (`wilson` in `report.py`). The interval is not a hypothesis test.

`change_exceeds_both_rerun_variations` is true only when all three rates exist and

```text
change_rate > max(current_rerun_rate, proposed_rerun_rate)
```

using those rounded rates. Equal rates do not exceed the floor. A missing second run makes the comparison `null`. Neither re-run rate is subtracted from the change. The same boolean is `execution_floor.change_exceeds_floor`.

Known values, locked by `tests/test_statistics.py`:

| Change | Current re-run | Proposed re-run | Floor | Exceeds |
|---|---:|---:|---:|---|
| 7/40 = 0.175 | 2/40 = 0.05 | 3/40 = 0.075 | 0.075 | yes |
| 1/5 = 0.2 | 0/5 = 0 | 2/5 = 0.4 | 0.4 | no |
| 0.2 | 0.2 | 0 | 0.2 | no (equal is not above) |
| any | missing | any | undefined | null |

Wilson 95% for 7/40 at `z = 1.959964` is 0.087454136985 to 0.319499904613.

## What this is not

The manuscript's exact test is not in this repository, so it is not restated here as a formula. Shipping a different formula under the same name would hide the gap. Until that test is specified in code from the preregistration, the package keeps the descriptive comparison above.

Two p-values in the exploratory notes were computed **outside** the package. They are two-sided exact McNemar/binomial tests of discordant correct/incorrect pairs, not a test against the re-execution floor:

| Note | Discordant pairs | p-value in the note |
|---|---|---|
| [Same-weights prompt update](research/same_weights_prompt_update_20261113.md) | 3 gains, 5 losses | 0.7265625 (186/256) |
| [Qwen/BoolQ audit](../experiments/qwen_cpu_pilot/SCIENTIFIC_AUDIT.md) | 16 improved, 6 worsened | about 0.05248 |

`tests/test_statistics.py` recomputes 186/256 and checks that a file with 5 stable regressions and 3 stable improvements still has no p-value in `summary.json`. The release gate does not use either figure.

## Where the numbers live

- Python: `src/ridi_check/statistics.py`, called from `build_summary` in `src/ridi_check/report.py`.
- The browser report shows the same rates and Wilson intervals. It does not add a p-value.
- Item labels are unchanged. `classify` in `src/ridi_check/analysis.py` is still the rule for stable, unstable, and unconfirmed.
