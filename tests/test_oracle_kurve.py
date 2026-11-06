"""Orakel-Test goodhart-kurve-demo: der Kern gegen einen ANDEREN Rechenweg (ORACLE-PLAYBOOK §2, DEMO-PLAYBOOK §12).

(1) Die Formel der Ordnungsstatistik gegen die vollständige Aufzählung aller N^k Ziehungen (Fraction, ganze Zahlen, mit Gleichständen in P);
(2) gegen eine unabhängige Monte-Carlo-Rechnung mit festem Seed; (3) Perzentil und Spearman gegen reines Python."""

import itertools
import random
from fractions import Fraction

import numpy as np
import pytest

import gdh_algorithm as A
import gdh_scenario as S


def _brute_force(p, t, k):
    """E[T] und E[P] über alle N^k Ziehungen mit Zurücklegen; der Gewinner ist der Plan mit kleinstem P, bei Gleichstand der mit kleinerem Index (Reihenfolge der Aufzählung)."""
    n = len(p)
    total_t, total_p = Fraction(0), Fraction(0)
    for draw in itertools.product(range(n), repeat=k):
        win = min(draw, key=lambda j: (p[j], j))
        total_t += int(t[win])
        total_p += int(p[win])
    return total_t / n ** k, total_p / n ** k


@pytest.mark.parametrize("seed,n_plans,kmax", [(1, 6, 4), (2, 6, 4), (3, 5, 5), (4, 8, 4), (5, 24, 3)])
def test_the_order_statistic_formula_matches_the_full_enumeration_of_all_draws(seed, n_plans, kmax):
    rng = np.random.default_rng(seed)
    p = rng.integers(1, 9, n_plans)                 # kleine ganze Zahlen: viele Gleichstände in P
    t = rng.integers(1, 30, n_plans)
    for k in range(1, kmax + 1):
        et_ref, ep_ref = _brute_force(p, t, k)
        et, ep = A.expected_curve(p, t, [k])
        assert et[0] == pytest.approx(float(et_ref), rel=1e-12) and ep[0] == pytest.approx(float(ep_ref), rel=1e-12), (seed, k)


def test_the_formula_in_exact_fractions_gives_the_same_number_as_the_float_code():
    p = [3, 1, 2, 1, 5, 4]
    t = [9, 4, 7, 8, 1, 6]
    order = sorted(range(6), key=lambda j: (p[j], j))
    for k in (1, 2, 3, 7):
        exact = sum((Fraction(6 - r + 1, 6) ** k - Fraction(6 - r, 6) ** k) * t[order[r - 1]] for r in range(1, 7))
        assert A.expected_curve(np.array(p), np.array(t), [k])[0][0] == pytest.approx(float(exact), rel=1e-14)


@pytest.mark.parametrize("k", [1, 4, 16, 64])
def test_a_seeded_monte_carlo_agrees_with_the_exact_expectation(k):
    p, t, _ = S.make_noise(5, 9, 40.0)
    et, ep = A.expected_curve(p, t, [k])
    rnd = random.Random(2024 + k)
    n = len(p)
    draws = 60000
    vals = []
    for _ in range(draws):
        win = min((rnd.randrange(n) for _ in range(k)), key=lambda j: (p[j], j))
        vals.append(t[win])
    mean, sd = float(np.mean(vals)), float(np.std(vals))
    assert abs(mean - et[0]) < 4.5 * sd / draws ** 0.5 + 1e-9


@pytest.mark.parametrize("n", [6, 8])
def test_two_to_the_twenty_is_practically_infinity(n):
    for model in ("noise", "hidden", "max"):
        p, t, _ = S.make_model(model, n, 100003, 25.0, -0.5, 2.0)
        et, _ = A.expected_curve(p, t, [2 ** 20, None])
        assert abs(et[0] - et[1]) <= 1e-9 * abs(et[1])


def test_the_percentile_and_the_optimum_match_plain_python():
    for seed in range(6):
        p, t, _ = S.make_hidden(5, seed, -0.4, 2.0)
        j = min(range(len(p)), key=lambda i: (p[i], i))
        ref = sum(1 for x in t if x <= t[j]) / len(t)
        assert A.percentile_of_optimum(p, t) == pytest.approx(ref)
        assert A.expected_curve(p, t, [None])[0][0] == pytest.approx(t[j])


def test_a_pure_python_curve_for_every_model_equals_the_vector_code():
    """Alles in einer Schleife ohne numpy-Vektoren: Gewichte, Erwartung, Minimum und Anstieg."""
    for model in ("noise", "hidden", "max"):
        p, t, _ = S.make_model(model, 5, 100005, 30.0, 0.3, 1.0)
        n = len(p)
        order = sorted(range(n), key=lambda j: (p[j], j))
        curve = []
        for e in range(0, 21):
            k = 2 ** e
            curve.append(sum(((n - r + 1) / n) ** k * float(t[order[r - 1]]) - ((n - r) / n) ** k * float(t[order[r - 1]]) for r in range(1, n + 1)))
        curve.append(float(t[order[0]]))
        et, _ = A.expected_curve(p, t)
        assert list(et) == pytest.approx(curve, rel=1e-9)
        lo = min(curve)
        st = A.curve_stats(et)
        assert st["min"] == pytest.approx(lo, rel=1e-9) and st["rise"] == pytest.approx((curve[-1] - lo) / lo, abs=1e-9)
