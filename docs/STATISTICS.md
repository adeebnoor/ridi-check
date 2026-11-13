# The execution floor and the exact test

This note says what ridi-check computes. The rounded-rate comparison is unchanged. The exact conditional test is added beside it and is labelled pending confirmation against the registered protocol.

## Terms

- **Matched items.** The same `case_id` is run on the current version and the proposed version. Rows are not paired by similarity after the fact.
- **Repeated runs.** Each version may be run more than once. The label "stable" requires every run of a version to agree with that version's first run, and at least two runs of both versions. Otherwise the item is `unstable`, or `unconfirmed` when a version was run once.
- **Execution floor.** The re-execution noise baseline: how often a version disagrees with itself. In this package that is the run-1 versus run-2 disagreement rate of each version. The floor rate is the larger of those two rates.
- **Exact conditional test.** A separate block, `exact_conditional_test`, tests whether item-level between-version changes exceed the run-to-run disagreements. Its status is **implementation pending confirmation against the registered protocol**. `execution_floor.exact_test_implemented` stays `false`: that flag belongs to the rounded-rate block, which still has no p-value.

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

## Exact conditional test

The rounded comparison above is unchanged. Beside it, `exact_conditional_test` reports a p-value and an effect.

**Status: implementation pending confirmation against the registered protocol.** The formula below is the exact conditional binomial test that matches the package's two runs per version. It is not a claim that the frozen analysis script does the same arithmetic.

### Formula this package runs

On every matched item with two runs of both versions (call that number N):

- `change` is 1 when run 1 of the current version differs from run 1 of the proposed version.
- A version's `re-run` is 1 when its own run 1 differs from its own run 2.
- For one version, `b` is the number of items with change 1 and re-run 0, and `c` is the number with change 0 and re-run 1.
- The one-sided exact p-value is P(B ≥ b) for B binomial with b + c trials and probability 1/2. The fraction has denominator 2^(b+c).
- The effect against that version is (b − c) / N, which equals the change rate minus that version's re-run rate.
- The effect against the floor is (change count − the larger of the two re-run counts) / N.
- The p-value for exceeding both versions is the larger of the two one-sided p-values.
- Items missing a second run of either version are excluded and counted. They are not treated as agreement.

The equality is the one `analyse` already uses: correctness when the file has an answer key, answers otherwise.

### Interval

Each arm's 95% interval is a Clopper–Pearson interval for b successes in b + c trials, transformed by (2π − 1) × (b + c) / N. That is an exact interval for the paired difference **given the discordant items**. Endpoints are then moved outward to the next 0.000000000001 so the displayed 12 decimals cannot sit inside the exact bounds.

The interval on the floor effect is the lower envelope of the two arm intervals, each computed at 97.5%. A Bonferroni bound then keeps joint coverage of at least 95%, still conditional on the discordant items. If either version has no discordant items, that interval is omitted rather than reported as a point.

### What the registrations actually specify

The commercial addendum at [osf.io/anbjd](https://osf.io/anbjd) (DOI [10.17605/OSF.IO/ANBJD](https://doi.org/10.17605/OSF.IO/ANBJD)) says H1c is the frozen one-sided within-benchmark bootstrap in `holdout_analysis.py`, SHA-256 `09fe6ee38e535205bc117aa6e212e7d31158cc3686cee776f38c2d7b24d11b3c`. That file is in the registration. Checked against the file:

- excess = equal-benchmark change rate − control rate, paired on the same items;
- the control is 1 when any of three executions of the same context disagree;
- 20,000 within-benchmark draws, seed 20261102;
- the p-value is the share of draws with excess ≤ 0.02;
- Holm across models at one-sided alpha 0.025;
- a separate Clopper–Pearson interval is reported for each marginal rate, not for the excess. The excess interval in that script is a bootstrap percentile interval.

[osf.io/7uzv5](https://osf.io/7uzv5) (DOI [10.17605/OSF.IO/7UZV5](https://doi.org/10.17605/OSF.IO/7UZV5)) is the RIDI-24 capture-share protocol. Its execution floor is an incumbent re-run. It does not state this conditional binomial test.

### What still has to be checked

- The manuscript text, when a preprint exists. The registrations do not include a sentence that names this conditional binomial test as the manuscript's test. They name the bootstrap.
- Whether a two-run file should use the current version only as the control, the proposed version only, or both. This package reports both, and the floor effect uses the larger re-run count.
- The 2 percentage-point margin, equal benchmark weights, three same-context executions, and Holm across models. None of those is applied here.
- The conditional interval is not the registered bootstrap interval, and it is not an unconditional interval for a larger population.

`tests/test_exact_conditional.py` locks the fractions. Two changes and no re-run disagreement on four items give p = 1/4 and effect 1/2. Three change-only items and one re-run-only item on eight items give p = 5/16 and effect 1/4.

### The exploratory 3-versus-5 and 16-versus-6 figures

Those notes are a different null: two-sided exact binomial tests of gains against losses, not a test against the re-execution floor. The same binomial function can evaluate them. It does not put them in `summary.json`.

| Note | Discordant pairs | Exact p-value |
|---|---|---|
| [Same-weights prompt update](research/same_weights_prompt_update_20261113.md) | 3 gains, 5 losses | 186/256 = 0.7265625 |
| [Qwen/BoolQ audit](../experiments/qwen_cpu_pilot/SCIENTIFIC_AUDIT.md) | 16 improved, 6 worsened | 13757/262144 = 0.05247879…, which is 0.05248 to five decimal places |

The audit's "about 0.05248" is that rounding. A file with 5 stable regressions and 3 stable improvements, and no re-run disagreement, has floor-test p = 1/256. It does not report 0.7265625.

The release gate does not read either figure. It reads the floor test only with `gate --exact-test`. The default gate is unchanged, and `--strict` does not turn the flag on. Alpha defaults to 0.05, one-sided. The gate fails when the test cannot be computed, or when the one-sided p-value for exceeding both re-run disagreements is greater than alpha. A p-value equal to alpha passes.

## Where the numbers live

- Python: `src/ridi_check/statistics.py`. `build_summary` in `src/ridi_check/report.py` writes both blocks.
- `exact_conditional_test()` and `exact_conditional_test_from_analysis()` are the library calls.
- The printed report and `report.html` show the p-value, the effect, and the interval from that block. They do not recompute it.
- The browser tool (`web/`) still shows the rounded rates and Wilson intervals. It does not run this test.
- Item labels are unchanged. `classify` in `src/ridi_check/analysis.py` is still the rule for stable, unstable, and unconfirmed.
