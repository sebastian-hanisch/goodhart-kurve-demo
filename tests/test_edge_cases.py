"""Randfälle: ein Plan, zwei Pläne, alle P gleich, sehr große Stärke, Grenzwerte der Kopula, jedes Modell bei jeder Größe."""

import numpy as np
import pytest

import gdh_algorithm as A
import gdh_constants as C
import gdh_evaluation as ev
import gdh_scenario as S


def test_a_single_plan_has_a_flat_curve():
    p, t = np.array([5.0]), np.array([7.0])
    et, ep = A.expected_curve(p, t)
    assert (et == 7.0).all() and (ep == 5.0).all()
    st = A.curve_stats(et)
    assert st["rise"] == 0 and not st["declines"] and not st["harm"] and st["gain"] == 0


def test_two_plans_by_hand():
    """P = (1, 2), T = (10, 4): der Optimierer wählt Plan 0. k = 1: E[T] = 7; k = 2: Gewicht von Rang 1 ist 3/4, E[T] = 3/4 · 10 + 1/4 · 4 = 8,5; k = unendlich: 10."""
    et, _ = A.expected_curve(np.array([1.0, 2.0]), np.array([10.0, 4.0]), [1, 2, None])
    assert list(et) == pytest.approx([7.0, 8.5, 10.0])
    st = A.curve_stats(A.expected_curve(np.array([1.0, 2.0]), np.array([10.0, 4.0]))[0])
    assert st["e"] == 0 and st["harm"] and st["declines"] and st["rise"] == pytest.approx(10 / 7 - 1)


def test_all_plans_with_equal_proxy_are_chosen_by_the_enumeration_order():
    p = np.full(6, 3.0)
    t = np.array([9.0, 1.0, 5.0, 5.0, 5.0, 5.0])
    et, ep = A.expected_curve(p, t, [1, 2, None])
    assert et[2] == 9.0 and et[0] == pytest.approx(t.mean()) and (ep == 3.0).all()
    assert A.curve_stats(A.expected_curve(p, t)[0])["harm"] == (9.0 > t.mean())


def test_a_huge_k_does_not_overflow_and_equals_the_optimum():
    p, t, _ = S.make_noise(6, 5, 30.0)
    et, _ = A.expected_curve(p, t, [10 ** 9, None])
    assert et[0] == pytest.approx(et[1], rel=1e-12) and np.isfinite(et).all()


@pytest.mark.parametrize("corr", [-1.0, -0.999, 0.0, 0.999, 1.0])
def test_the_copula_limits_are_valid(corr):
    p, t, mats = S.make_hidden(5, 3, corr, 1.0)
    assert np.isfinite(p).all() and np.isfinite(t).all()
    if abs(corr) == 1.0:
        a, h = mats["A"], mats["H"]
        assert np.allclose(h, a) if corr == 1.0 else np.allclose(h, 100.0 - a, atol=1e-9)


@pytest.mark.parametrize("model", range(3))
@pytest.mark.parametrize("n", [3, 4, 8])
def test_every_model_runs_every_experiment_at_the_range_limits(model, n):
    for sigma, corr, w, k_exp in ((0, -90, 1, 0), (100, 90, 4, 21), (50, 0, 2, 13)):
        a = ev.analyse(ev.Settings(n, model, 1, sigma, corr, w, k_exp))
        st, cur = ev.summary(a), ev.current(a)
        ev.verdict_curve(st), ev.verdict_current(cur, st), ev.verdict_gap(st)
        assert len(ev.curve_rows(a)) == C.K_EXP_MAX - C.K_EXP_MIN + 1
        assert len(ev.model_compare(a)) == 3
        ev.verdict_models(ev.model_compare(a))
        f = ev.fresh_check(a)
        assert (f is None) == (model != 0)
        if f:
            ev.verdict_fresh(f)


def test_the_max_model_has_no_promise_gap():
    a = ev.analyse(ev.Settings(6, 2, 100000, 50, 0, 1, 21))
    assert not ev.comparable("max") and ev.comparable("noise") and ev.comparable("hidden")
    assert ev.current(a)["gap"] is None and ev.summary(a)["gap_inf"] is None and all(r["gap"] is None for r in ev.curve_rows(a))
    assert ev.verdict_gap(ev.summary(a))[0] == "info"


def test_zero_sigma_gives_no_promise_gap_and_the_optimum_is_the_true_optimum():
    a = ev.analyse(ev.Settings(6, 0, 100000, 0, 0, 1, 21))
    st = ev.summary(a)
    assert st["gap_inf"] == pytest.approx(0.0, abs=1e-12) and st["p_opt_is_t_best"] and not st["declines"] and st["percentile"] == pytest.approx(1 / 720)


def test_unknown_model_raises_and_the_enumeration_limit_is_nine():
    with pytest.raises(ValueError):
        S.make_model("rauschen", 4, 1)
    with pytest.raises(ValueError):
        S.all_plans(10)
    assert len(S.all_plans(4)) == 24 and C.N_MAX == 8


def test_k_exp_extremes_pick_the_first_and_the_last_point_of_the_curve():
    a0 = ev.analyse(ev.Settings(5, 0, 3, 50, 0, 1, 0))
    a21 = ev.analyse(ev.Settings(5, 0, 3, 50, 0, 1, 21))
    assert ev.current(a0)["et"] == pytest.approx(a0.t.mean()) and ev.current(a21)["et"] == pytest.approx(a21.t[int(np.argmin(a21.p))])
