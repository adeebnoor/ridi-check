"""Execution floor as shipped, plus an exact conditional test beside it.

The rounded-rate comparison below is unchanged. It does not return a p-value.
It records the descriptive comparison already used by ``report``:

- matched items are the cases compared on both versions;
- repeated runs supply a re-execution rate for each version (run 1 against run 2);
- the execution floor is the larger of those two rates;
- each rate is the value rounded to 6 decimal places;
- the change "exceeds the floor" only when the between-version rate is strictly
  greater than both re-run rates.

Neither re-run rate is subtracted from the change. A missing repeated run makes
the comparison undefined. The release gate does not read this comparison.

The exploratory McNemar p-values quoted in ``docs/research/`` were computed
outside this package. They test a different null (balanced improvements and
regressions) and are not the rounded-rate comparison.

``exact_conditional_test`` is a separate statistic. It is an exact conditional
binomial (McNemar) test of item-level change against each version's run-1
versus run-2 disagreement. Its status is ``PENDING_CONFIRMATION``: the
preregistered analysis script is a paired bootstrap with a different floor,
and this function does not reproduce that script. See ``docs/STATISTICS.md``.
"""

from __future__ import annotations

import math
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal, localcontext
from fractions import Fraction

EXACT_TEST_IMPLEMENTED = False
RATE_DECIMALS = 6
PENDING_CONFIRMATION = "implementation pending confirmation against the registered protocol"
_DECIMAL_PLACES = Decimal("1e-12")


def rounded_rate(count: int, n: int) -> float | None:
    """``count / n`` rounded to 6 decimal places, or None when ``n`` is 0."""
    if n <= 0:
        return None
    return round(count / n, RATE_DECIMALS)


def change_exceeds_execution_floor(
    change_rate: float,
    current_rerun_rate: float | None,
    proposed_rerun_rate: float | None,
) -> bool | None:
    """True when ``change_rate`` is strictly above both repeated-run rates.

    The rates are already rounded to 6 decimal places. None if either repeated-run
    rate is missing. This is not a p-value and not the manuscript's exact test.
    """
    if current_rerun_rate is None or proposed_rerun_rate is None:
        return None
    return change_rate > max(current_rerun_rate, proposed_rerun_rate)


def execution_floor_record(
    change_rate: float,
    current_rerun_rate: float | None,
    proposed_rerun_rate: float | None,
) -> dict:
    """The execution-floor block written to ``summary.json``."""
    exceeds = change_exceeds_execution_floor(change_rate, current_rerun_rate, proposed_rerun_rate)
    floor = None if exceeds is None else max(current_rerun_rate, proposed_rerun_rate)
    return {
        "name": "execution floor",
        "kind": "descriptive comparison of rates rounded to 6 decimal places",
        "exact_test_implemented": EXACT_TEST_IMPLEMENTED,
        "floor_rate": floor,
        "change_rate": change_rate,
        "change_exceeds_floor": exceeds,
        "current_rerun_rate": current_rerun_rate,
        "proposed_rerun_rate": proposed_rerun_rate,
        "note": (
            "The execution floor is the larger run-1 versus run-2 disagreement rate. "
            "The between-version rate is not reduced by it. No exact test is computed, "
            "and the release gate does not use this comparison."
        ),
    }


# --- exact conditional test (added beside the rounded-rate comparison) ---

FORMULA = (
    "On every matched item with two runs of both versions, change is 1 when the first runs "
    "differ between versions, and a version's re-run is 1 when its run 1 differs from its run 2. "
    "For one version, b is the number of items with change 1 and re-run 0, and c is the number "
    "with change 0 and re-run 1. The one-sided exact p-value is P(B >= b) for B binomial with "
    "b + c trials and probability 1/2. The effect against that version is (b - c) / N. "
    "The effect against the floor is (change count - the larger re-run count) / N. "
    "The p-value for exceeding both versions is the larger of the two one-sided p-values. "
    "Each interval transforms a Clopper-Pearson interval for b successes in b + c trials by "
    "(2*pi - 1) * (b + c) / N, then moves the endpoints outward to 12 decimal places. "
    "The floor interval is the lower envelope of the two intervals, each computed at 97.5% "
    "so that a Bonferroni bound keeps joint coverage of at least 95%."
)

_PROTOCOL = {
    "reproduced": False,
    "sources": [
        "osf.io/anbjd",
        "doi.org/10.17605/OSF.IO/ANBJD",
        "osf.io/7uzv5",
        "doi.org/10.17605/OSF.IO/7UZV5",
    ],
    "frozen_script": "holdout_analysis.py",
    "frozen_script_sha256": "09fe6ee38e535205bc117aa6e212e7d31158cc3686cee776f38c2d7b24d11b3c",
    "must_check": [
        "The frozen script tests P(excess <= 0.02) with 20,000 within-benchmark paired bootstrap draws, seed 20261102, equal benchmark weights, and Holm across models at one-sided alpha 0.025. This function does not run that bootstrap.",
        "The registered control is 1 when any of three same-context executions disagree. This function uses run 1 against run 2 of each version, on items that have two runs of both.",
        "A results file has no benchmark column, so equal-benchmark weights are not applied.",
        "Holm adjustment across models is not applied. One file is one comparison.",
        "The registered margin is 2 percentage points. This null is equality of the paired rates.",
        "The registered analysis scores correctness. No-key mode compares answers with the same equality the report already uses.",
        "RIDI-24 (osf.io/7uzv5) uses an incumbent re-run floor for a capture-share study. It does not state this conditional binomial test.",
        "The conditional interval is exact for the paired difference given the discordant items. It is not the registered bootstrap percentile interval.",
        "Whether the manuscript's prose names this test or the bootstrap still has to be checked against the manuscript when a preprint exists.",
    ],
}


def _counts(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def binomial_p_at_least(successes: int, trials: int) -> Fraction:
    """P(X >= successes) for X binomial with ``trials`` and probability 1/2.

    The value is an exact fraction with denominator 2**trials. A trial count of 0
    gives 1 when ``successes`` is 0, and 0 otherwise.
    """
    successes, trials = _counts("successes", successes), _counts("trials", trials)
    if successes > trials:
        return Fraction(0)
    if successes == 0:
        return Fraction(1)
    term = math.comb(trials, successes)
    total = term
    for index in range(successes, trials):
        term = term * (trials - index) // (index + 1)
        total += term
    return Fraction(total, 1 << trials)


def binomial_two_sided_as_or_less_likely(successes: int, trials: int) -> Fraction:
    """Two-sided exact binomial p-value: outcomes whose probability is at most the observed one's.

    This is the gains-versus-losses null used in the exploratory notes (3 versus 5 is
    186/256). It is not the execution-floor test.
    """
    successes, trials = _counts("successes", successes), _counts("trials", trials)
    if successes > trials:
        raise ValueError("successes cannot exceed trials")
    if trials == 0:
        return Fraction(1)
    threshold = math.comb(trials, successes)
    total = sum(math.comb(trials, k) for k in range(trials + 1) if math.comb(trials, k) <= threshold)
    return Fraction(total, 1 << trials)


def _away_from_zero(value: Decimal) -> Decimal:
    """Keep a continued-fraction term from becoming zero."""
    if value == 0:
        return Decimal("1e-30")
    return value


def _ln_beta(a: int, b: int) -> Decimal:
    """Natural log of B(a, b) for positive integers, in the current decimal context."""
    last = a + b - 1
    acc = Decimal(0)
    facts = [Decimal(0)] * (last + 1)
    for i in range(2, last + 1):
        acc += Decimal(i).ln()
        facts[i] = acc
    return facts[a - 1] + facts[b - 1] - facts[last]


def _betacf(a: int, b: int, x: Decimal) -> Decimal:
    """Continued fraction used by the regularized incomplete beta (Numerical Recipes)."""
    aa_ = Decimal(a)
    bb = Decimal(b)
    qab = aa_ + bb
    qap = aa_ + 1
    qam = aa_ - 1
    c = Decimal(1)
    d = _away_from_zero(Decimal(1) - qab * x / qap)
    d = 1 / d
    h = d
    for m in range(1, 301):
        m2 = 2 * m
        aa = Decimal(m) * (bb - Decimal(m)) * x / ((qam + m2) * (aa_ + m2))
        d = _away_from_zero(1 + aa * d)
        c = _away_from_zero(1 + aa / c)
        d = 1 / d
        h *= d * c
        aa = -(aa_ + Decimal(m)) * (qab + Decimal(m)) * x / ((aa_ + m2) * (qap + m2))
        d = _away_from_zero(1 + aa * d)
        c = _away_from_zero(1 + aa / c)
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < Decimal("1e-25"):
            return h
    raise ValueError("the incomplete-beta continued fraction did not converge")


def _reg_incbeta(a: int, b: int, x: Decimal, ln_beta: Decimal) -> Decimal:
    """Regularized incomplete beta I_x(a, b). ``ln_beta`` is ln B(a, b)."""
    if x <= 0:
        return Decimal(0)
    if x >= 1:
        return Decimal(1)
    front = (Decimal(a) * x.ln() + Decimal(b) * (Decimal(1) - x).ln() - ln_beta).exp()
    if x < (Decimal(a) + 1) / (Decimal(a) + Decimal(b) + 2):
        return front * _betacf(a, b, x) / Decimal(a)
    other = (Decimal(b) * (Decimal(1) - x).ln() + Decimal(a) * x.ln() - ln_beta).exp()
    return Decimal(1) - other * _betacf(b, a, Decimal(1) - x) / Decimal(b)


def _beta_ppf(probability: Decimal, a: int, b: int) -> Decimal:
    """Quantile of the Beta(a, b) distribution for positive integers a and b."""
    if probability <= 0:
        return Decimal(0)
    if probability >= 1:
        return Decimal(1)
    if b == 1:
        return probability ** (Decimal(1) / Decimal(a))
    if a == 1:
        return Decimal(1) - (Decimal(1) - probability) ** (Decimal(1) / Decimal(b))
    ln_beta = _ln_beta(a, b)
    low, high = Decimal(0), Decimal(1)
    for _ in range(80):
        mid = (low + high) / 2
        if _reg_incbeta(a, b, mid, ln_beta) < probability:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def clopper_pearson(successes: int, trials: int, *, confidence: Decimal | str = "0.95") -> tuple[Decimal, Decimal]:
    """Clopper-Pearson interval for ``successes`` out of ``trials``.

    ``confidence`` is the two-sided level, for example ``"0.95"`` or ``"0.975"``.
    The endpoints are the beta quantiles, not yet rounded.
    """
    successes, trials = _counts("successes", successes), _counts("trials", trials)
    if successes > trials:
        raise ValueError("successes cannot exceed trials")
    if trials == 0:
        raise ValueError("a Clopper-Pearson interval needs at least one trial")
    with localcontext() as ctx:
        ctx.prec = 50
        level = Decimal(confidence)
        if not (Decimal(0) < level < Decimal(1)):
            raise ValueError("confidence must be strictly between 0 and 1")
        tail = (Decimal(1) - level) / 2
        low = Decimal(0) if successes == 0 else _beta_ppf(tail, successes, trials - successes + 1)
        high = Decimal(1) if successes == trials else _beta_ppf(Decimal(1) - tail, successes + 1, trials - successes)
        return low, high


def _outward(low: Decimal, high: Decimal) -> tuple[str, str]:
    """Move endpoints out to the next 1e-12 and clamp them to [-1, 1]."""
    with localcontext() as ctx:
        ctx.prec = 50
        lo = (low / _DECIMAL_PLACES).to_integral_value(ROUND_FLOOR) * _DECIMAL_PLACES
        hi = (high / _DECIMAL_PLACES).to_integral_value(ROUND_CEILING) * _DECIMAL_PLACES
        lo = max(Decimal("-1"), lo)
        hi = min(Decimal("1"), hi)
        return f"{lo:.12f}", f"{hi:.12f}"


def _ratio(numerator: int, denominator: int) -> dict:
    """An exact reduced fraction, a 12-decimal rendering, and a short display string.

    Numerator and denominator are strings so a report page does not read them as
    floating-point numbers. The fraction is the value. ``decimal_12dp`` is
    half-even rounding of that fraction and is not a substitute for it.
    """
    value = Fraction(numerator, denominator)
    with localcontext() as ctx:
        ctx.prec = 50
        dec = (Decimal(value.numerator) / Decimal(value.denominator)).quantize(_DECIMAL_PLACES, ROUND_HALF_EVEN)
    return {
        "numerator": str(value.numerator),
        "denominator": str(value.denominator),
        "decimal_12dp": f"{dec:.12f}",
        "display": _display(value),
    }


def _display(value: Fraction) -> str:
    den = value.denominator
    if value.numerator == 1 and den > 1 and den & (den - 1) == 0:
        exp = den.bit_length() - 1
        if exp >= 16:
            return f"1/2^{exp}"
    if den <= 1_000_000:
        return f"{value.numerator}/{den}"
    with localcontext() as ctx:
        ctx.prec = 50
        dec = (Decimal(value.numerator) / Decimal(den)).quantize(_DECIMAL_PLACES, ROUND_HALF_EVEN)
    return f"{dec:.12f}"


def ratio_fraction(record: dict) -> Fraction:
    """The exact fraction stored by :func:`_ratio`."""
    return Fraction(int(record["numerator"]), int(record["denominator"]))


def _paired_interval(change_only: int, floor_only: int, n_items: int, confidence: str) -> dict | None:
    """Conditional Clopper-Pearson interval for (change_only - floor_only) / n_items."""
    discordant = change_only + floor_only
    if discordant == 0 or n_items <= 0:
        return None
    low, high = clopper_pearson(change_only, discordant, confidence=confidence)
    scale = Decimal(discordant) / Decimal(n_items)
    lo, hi = _outward((2 * low - 1) * scale, (2 * high - 1) * scale)
    return {
        "low": lo,
        "high": hi,
        "confidence": confidence,
        "method": (
            "Clopper-Pearson interval for the change-only share of the discordant items, "
            "transformed to (2*pi - 1) * (discordant items) / N, then moved outward to 12 decimal places. "
            "Conditional on the discordant items."
        ),
    }


def _arm(change_only: int, floor_only: int, n_items: int) -> dict:
    p = Fraction(1) if change_only + floor_only == 0 else binomial_p_at_least(change_only, change_only + floor_only)
    return {
        "change_only": change_only,
        "floor_only": floor_only,
        "concordant": n_items - change_only - floor_only,
        "p_value_one_sided": _ratio(p.numerator, p.denominator),
        "effect_change_rate_minus_rerun_rate": _ratio(change_only - floor_only, n_items),
        "interval_95": _paired_interval(change_only, floor_only, n_items, "0.95"),
    }


def _floor_interval(current: dict, proposed: dict, n_items: int, change_only_c: int, floor_only_c: int,
                    change_only_p: int, floor_only_p: int) -> dict | None:
    """Bonferroni envelope of the two 97.5% conditional intervals, for the smaller difference."""
    if current["interval_95"] is None or proposed["interval_95"] is None:
        return None
    left = _paired_interval(change_only_c, floor_only_c, n_items, "0.975")
    right = _paired_interval(change_only_p, floor_only_p, n_items, "0.975")
    if left is None or right is None:
        return None
    low = min(Decimal(left["low"]), Decimal(right["low"]))
    high = min(Decimal(left["high"]), Decimal(right["high"]))
    return {
        "low": f"{low:.12f}",
        "high": f"{high:.12f}",
        "confidence": "0.95",
        "method": (
            "Lower envelope of two conditional Clopper-Pearson intervals, each at 97.5%. "
            "By a Bonferroni bound this covers the smaller of the two paired differences "
            "at least 95% of the time, conditional on both discordant sets. "
            "Endpoints are moved outward to 12 decimal places. "
            "This is not the registered bootstrap percentile interval."
        ),
    }


def exact_conditional_test(
    pairs: list[tuple[int, int, int]], *, excluded_missing_second_run: int = 0, comparison: str = "correctness",
) -> dict:
    """Exact conditional test of between-version change against each version's re-run.

    ``pairs`` are ``(change, current_rerun, proposed_rerun)``, each 0 or 1, on items
    that have two runs of both versions. ``comparison`` is ``"correctness"`` or
    ``"answers"``. The returned object is the ``exact_conditional_test`` block.
    """
    if comparison not in ("correctness", "answers"):
        raise ValueError("comparison must be 'correctness' or 'answers'")
    excluded_missing_second_run = _counts("excluded_missing_second_run", excluded_missing_second_run)
    cleaned: list[tuple[int, int, int]] = []
    for index, row in enumerate(pairs):
        if len(row) != 3:
            raise ValueError(f"pair {index} must hold three indicators")
        cleaned.append(tuple(_counts(f"pair {index}", bit) for bit in row))  # type: ignore[misc]
        if any(bit not in (0, 1) for bit in cleaned[-1]):
            raise ValueError(f"pair {index} indicators must be 0 or 1")
    record = {
        "name": "exact conditional binomial test",
        "status": PENDING_CONFIRMATION,
        "comparison": comparison,
        "alternative": "one-sided: more between-version changes than re-run disagreements",
        "n_items": len(cleaned),
        "excluded_missing_second_run": excluded_missing_second_run,
        "formula": FORMULA,
        "registered_protocol": {
            "reproduced": False,
            "sources": list(_PROTOCOL["sources"]),
            "frozen_script": _PROTOCOL["frozen_script"],
            "frozen_script_sha256": _PROTOCOL["frozen_script_sha256"],
            "must_check": list(_PROTOCOL["must_check"]),
        },
    }
    if not cleaned:
        record.update({
            "change_count": 0,
            "current_rerun_count": 0,
            "proposed_rerun_count": 0,
            "versus_current": None,
            "versus_proposed": None,
            "exceeds_both": None,
        })
        return record
    change = sum(row[0] for row in cleaned)
    current = sum(row[1] for row in cleaned)
    proposed = sum(row[2] for row in cleaned)
    b_c = sum(1 for row in cleaned if row[0] == 1 and row[1] == 0)
    c_c = sum(1 for row in cleaned if row[0] == 0 and row[1] == 1)
    b_p = sum(1 for row in cleaned if row[0] == 1 and row[2] == 0)
    c_p = sum(1 for row in cleaned if row[0] == 0 and row[2] == 1)
    n = len(cleaned)
    versus_current = _arm(b_c, c_c, n)
    versus_proposed = _arm(b_p, c_p, n)
    p_current = ratio_fraction(versus_current["p_value_one_sided"])
    p_proposed = ratio_fraction(versus_proposed["p_value_one_sided"])
    larger = p_current if p_current >= p_proposed else p_proposed
    if current > proposed:
        which = "current"
    elif proposed > current:
        which = "proposed"
    else:
        which = "tie"
    record.update({
        "change_count": change,
        "current_rerun_count": current,
        "proposed_rerun_count": proposed,
        "versus_current": versus_current,
        "versus_proposed": versus_proposed,
        "exceeds_both": {
            "p_value_one_sided": _ratio(larger.numerator, larger.denominator),
            "effect_change_minus_larger_rerun_rate": _ratio(change - max(current, proposed), n),
            "larger_rerun": which,
            "interval_95": _floor_interval(versus_current, versus_proposed, n, b_c, c_c, b_p, c_p),
        },
    })
    return record


def exact_conditional_test_from_analysis(analysis) -> dict:
    """The exact conditional test for one :class:`~ridi_check.analysis.Analysis`."""
    from .analysis import INCOMPLETE, KEY, make_eq

    eq = make_eq(analysis.mode, analysis.threshold)
    pairs: list[tuple[int, int, int]] = []
    excluded = 0
    for case, state in analysis.items:
        if state == INCOMPLETE:
            continue
        current, proposed = case.baseline, case.updated
        if len(current) < 2 or len(proposed) < 2:
            excluded += 1
            continue
        pairs.append((
            0 if eq(current[0], proposed[0]) else 1,
            0 if eq(current[0], current[1]) else 1,
            0 if eq(proposed[0], proposed[1]) else 1,
        ))
    return exact_conditional_test(
        pairs,
        excluded_missing_second_run=excluded,
        comparison="correctness" if analysis.mode == KEY else "answers",
    )


def exact_test_lines(record: dict) -> list[str]:
    """Lines ``report`` prints after the rounded-rate sentences."""
    if record["n_items"] == 0:
        return [
            "Exact conditional test: not computed. No matched item has two runs of both versions. "
            f"Status: {PENDING_CONFIRMATION}."
        ]
    both = record["exceeds_both"]
    interval = both["interval_95"]
    span = (
        "undefined, because a version has no discordant items"
        if interval is None else f"{interval['low']} to {interval['high']}"
    )
    return [
        "Exact conditional test (one-sided): p = "
        f"{both['p_value_one_sided']['display']} that the between-version change exceeds both "
        f"run-to-run disagreements on {record['n_items']} matched items. "
        "Change rate minus the larger re-run rate = "
        f"{both['effect_change_minus_larger_rerun_rate']['display']} "
        f"(conditional 95% interval {span}).",
        f"Status: {PENDING_CONFIRMATION}. This does not replace the rounded-rate comparison above.",
    ]
