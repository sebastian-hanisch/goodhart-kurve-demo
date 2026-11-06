"""Handwerte: jede Einheit des Kerns an einem Beispiel, das von Hand nachgerechnet ist (DEMO-PLAYBOOK §1b)."""

import itertools
from fractions import Fraction

import numpy as np
import pytest

import gdh_algorithm as A
import gdh_constants as C
import gdh_evaluation as ev
import gdh_scenario as S

PLANS = list(itertools.permutations(range(3)))
HAND = {(0, 1, 2): (10, 17), (0, 2, 1): (13, 24), (1, 0, 2): (8, 14), (1, 2, 0): (16, 25), (2, 0, 1): (7, 20), (2, 1, 0): (12, 24)}


def test_hand_example_sums_of_all_six_plans(hand_p, hand_t):
    for k, plan in enumerate(PLANS):
        assert (int(hand_p[k]), int(hand_t[k])) == HAND[plan]


def test_hand_example_weights_for_one_two_and_infinity():
    assert list(A.weights(6, 1)) == pytest.approx([1 / 6] * 6)
    assert list(A.weights(6, 2)) == pytest.approx([11 / 36, 9 / 36, 7 / 36, 5 / 36, 3 / 36, 1 / 36])
    assert list(A.weights(6, None)) == [1, 0, 0, 0, 0, 0]
    for k in (1, 2, 3, 4, 8, 100):
        assert A.weights(6, k).sum() == pytest.approx(1.0)


def test_hand_example_expected_values_of_t_and_p(hand_p, hand_t):
    et, ep = A.expected_curve(hand_p, hand_t, [1, 2, 4, None])
    assert list(et) == pytest.approx([62 / 3, 341 / 18, 11753 / 648, 20.0], rel=1e-12)
    assert list(ep) == pytest.approx([11.0, 167 / 18, 8.016975308641975, 7.0], rel=1e-12)
    assert float(Fraction(62, 3)) == pytest.approx(et[0])


def test_hand_example_curve_stats_minimum_at_four_then_rise(hand_p, hand_t):
    et, _ = A.expected_curve(hand_p, hand_t)
    st = A.curve_stats(et)
    assert st["k"] == 4 and st["e"] == 2 and st["declines"] and not st["harm"]
    assert st["min"] == pytest.approx(11753 / 648) and st["rise"] == pytest.approx((20 - 11753 / 648) / (11753 / 648))
    assert st["gain"] == pytest.approx((62 / 3 - 11753 / 648) / (62 / 3))


def test_hand_example_summary_gap_percentile_and_best_plan(hand_analysis):
    st = ev.summary(hand_analysis)
    assert st["p_opt"] == 7 and st["t_of_p_opt"] == 20 and st["t_best"] == 14 and not st["p_opt_is_t_best"]
    assert st["gap_inf"] == pytest.approx(13 / 20) and st["percentile"] == pytest.approx(3 / 6)
    assert PLANS[st["idx_p"]] == (2, 0, 1) and PLANS[st["idx_t"]] == (1, 0, 2)
    cur = ev.current(hand_analysis)
    assert cur["e"] == 21 and cur["et"] == 20.0 and cur["ep"] == 7.0 and cur["vs_1"] == pytest.approx((20 - 62 / 3) / (62 / 3))


def test_hand_example_spearman_matches_a_pure_python_rank_correlation(hand_p, hand_t):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r, i = [0.0] * len(v), 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for m in range(i, j + 1):
                r[order[m]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rp, rt = ranks(list(hand_p)), ranks(list(hand_t))
    mp, mt = sum(rp) / 6, sum(rt) / 6
    cov = sum((a - mp) * (b - mt) for a, b in zip(rp, rt))
    ref = cov / (sum((a - mp) ** 2 for a in rp) ** 0.5 * sum((b - mt) ** 2 for b in rt) ** 0.5)
    assert A.rank_correlation(hand_p, hand_t) == pytest.approx(ref)
    assert rt[PLANS.index((1, 0, 2))] == 1 and rt[PLANS.index((2, 1, 0))] == rt[PLANS.index((0, 2, 1))] == 4.5


def test_order_by_is_stable_for_ties():
    p = np.array([3, 1, 2, 1, 3])
    assert list(A.order_by(p)) == [1, 3, 2, 0, 4]


def test_ks_grid_and_k_text():
    assert A.KS_ALL[0] == 1 and A.KS_ALL[20] == 2 ** 20 and A.KS_ALL[21] is None and len(A.KS_ALL) == 22
    assert ev.k_text(0) == "1" and ev.k_text(3) == "8" and ev.k_text(4) == "2^4" and ev.k_text(20) == "2^20" and ev.k_text(21) == "∞"
    assert A.ks_for_exps([0, 1, 21]) == [1, 2, None]


def test_models_are_deterministic_and_shaped():
    for model in C.MODELS:
        p1, t1, m1 = S.make_model(model, 5, 7, 30.0, 0.5, 2.0)
        p2, t2, _ = S.make_model(model, 5, 7, 30.0, 0.5, 2.0)
        assert p1.shape == t1.shape == (120,) and (p1 == p2).all() and (t1 == t2).all() and "A" in m1
    with pytest.raises(ValueError):
        S.make_model("unbekannt", 5, 1)
    with pytest.raises(ValueError):
        S.all_plans(10)


def test_noise_with_zero_sigma_is_the_true_objective_and_max_is_not_the_sum():
    p, t, _ = S.make_noise(5, 3, 0.0)
    assert (p == t).all()
    p, t, mats = S.make_max(5, 3)
    assert (t <= p + 1e-9).all() and t.max() <= mats["A"].max() + 1e-9
    p, t, _ = S.make_hidden(5, 3, 0.0, 1.0)
    assert (t > p).all()


def test_text_helpers_format_numbers_with_a_decimal_comma():
    assert ev.de(3.14159, 2) == "3,14" and ev.de(-0.0001) == "0,0" and ev.pct(0.5909) == "59,1 %" and ev.pct(1.55, 0) == "155 %"


def test_fresh_check_is_available_only_for_noise_and_near_the_truth(hand_analysis):
    assert ev.fresh_check(hand_analysis) is None
    a = ev.analyse(ev.Settings(6, 0, 11, 50, 0, 1, 21))
    f = ev.fresh_check(a)
    assert f["draws"] == C.FRESH_DRAWS and abs(f["fresh_mean"] - f["true"]) < 4 * f["fresh_sd"] / f["draws"] ** 0.5 and f["claimed"] < f["true"]
    assert ev.fresh_check(a) == f
