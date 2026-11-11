# Test fixtures

`synthetic_fixture.csv` is synthetic. Its 40 cases were written by hand to cover every case state;
the answers (`YES`, `NO`, `UNSURE`) and the case ids do not come from any model, dataset or study.

What the tests expect from it:

| | Answer-key mode | No-key mode |
|---|---|---|
| Stable | 3 regressions (s05, s17, s29), 2 improvements (s11, s33) | 7 changes (s05, s11, s17, s24, s29, s33, s40) |
| Unstable | 5 (s03, s14, s22, s31, s38) | 5 (the same cases) |
| No change | 6 wrong in both, 24 correct in both | 28 same |
| First run | accuracy 30/40 to 29/40; 4 regressions, 3 improvements; change 7/40 | change 9/40 |
| Re-run variation | current 2/40, proposed 3/40 | current 2/40, proposed 3/40 |

s24 and s40 are wrong in both versions with a different wrong answer after the update.
