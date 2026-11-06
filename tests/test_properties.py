"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für jede Instanz gelten müssen, an festen Seeds und allen Modellen."""

import numpy as np
import pytest

import gdh_algorithm as A
import gdh_constants as C
import gdh_evaluation as ev
import gdh_scenario as S

CASES = [(model, n, seed) for model in C.MODELS for n in (3, 5, 6) for seed in range(3)]


def _pt(model, n, seed):
    return S.make_model(model, n, 100000 + seed, 40.0, -0.5, 2.0)[:2]


@pytest.mark.parametrize("n_plans", [1, 2, 6, 24, 120])
def test_weights_are_probabilities_that_sum_to_one_and_concentrate_on_rank_one(n_plans):
    for k in (1, 2, 5, 33, 1000):
        w = A.weights(n_plans, k)
        assert (w >= 0).all() and w.sum() == pytest.approx(1.0)
        assert (np.diff(w) <= 1e-15).all()               # je schlechter der Rang, desto unwahrscheinlicher
    assert A.weights(n_plans, 1) == pytest.approx([1 / n_plans] * n_plans)
    assert A.weights(n_plans, 10 ** 6)[0] == pytest.approx(1.0) or n_plans > 100


@pytest.mark.parametrize("model,n,seed", CASES)
def test_one_draw_is_the_mean_of_all_plans_and_every_expectation_stays_in_range(model, n, seed):
    p, t = _pt(model, n, seed)
    et, ep = A.expected_curve(p, t)
    assert et[0] == pytest.approx(t.mean()) and ep[0] == pytest.approx(p.mean())
    assert (et >= t.min() - 1e-9).all() and (et <= t.max() + 1e-9).all()


@pytest.mark.parametrize("model,n,seed", CASES)
def test_the_promise_never_gets_worse_with_more_optimization(model, n, seed):
    p, t = _pt(model, n, seed)
    _, ep = A.expected_curve(p, t)
    assert (np.diff(ep) <= 1e-9).all() and ep[-1] == pytest.approx(p.min())


@pytest.mark.parametrize("model,n,seed", CASES)
def test_when_the_proxy_is_the_truth_the_curve_falls_and_ends_at_the_optimum(model, n, seed):
    p, _ = _pt(model, n, seed)
    et, _ = A.expected_curve(p, p)
    assert (np.diff(et) <= 1e-9).all() and et[-1] == pytest.approx(et.min(), abs=1e-9) and not A.curve_stats(et)["declines"]


@pytest.mark.parametrize("model,n,seed", CASES)
def test_when_the_proxy_runs_against_the_truth_the_curve_only_rises(model, n, seed):
    p, _ = _pt(model, n, seed)
    et, _ = A.expected_curve(p, -p)
    assert (np.diff(et) >= -1e-9).all()
    et2, _ = A.expected_curve(p, 1000.0 - p)               # positive Kosten, gegenläufig
    st = A.curve_stats(et2)
    assert st["index"] == 0 and st["harm"] and st["declines"]


@pytest.mark.parametrize("model,n,seed", CASES)
def test_the_expectation_does_not_depend_on_the_order_of_the_plans_and_scales_linearly(model, n, seed):
    p, t = _pt(model, n, seed)
    et, ep = A.expected_curve(p, t)
    perm = np.random.default_rng(seed).permutation(len(p))
    et2, ep2 = A.expected_curve(p[perm], t[perm])
    assert et2 == pytest.approx(et, rel=1e-9) and ep2 == pytest.approx(ep, rel=1e-9)         # reell: keine Gleichstände in P
    et3, _ = A.expected_curve(p, 3.0 * t + 5.0)
    assert et3 == pytest.approx(3.0 * et + 5.0, rel=1e-9)


@pytest.mark.parametrize("seed", range(4))
def test_a_proxy_with_zero_noise_has_no_gap_and_more_noise_a_larger_gap_at_the_optimum(seed):
    gaps = []
    for sigma in (0.0, 10.0, 50.0, 150.0):
        p, t, _ = S.make_noise(6, 100000 + seed, sigma)
        et, ep = A.expected_curve(p, t, [None])
        gaps.append((et[0] - ep[0]) / et[0])
    assert gaps[0] == pytest.approx(0.0, abs=1e-12) and gaps[1] > 0 and gaps[3] > gaps[1]


@pytest.mark.parametrize("seed", range(3))
def test_summary_fields_are_consistent_with_the_curve(seed):
    for model in range(3):
        a = ev.analyse(ev.Settings(6, model, 100000 + seed, 50, -50, 2, 8))
        st = ev.summary(a)
        assert st["min"] == pytest.approx(a.et.min()) and st["et_inf"] == pytest.approx(a.et[-1]) and st["et_1"] == pytest.approx(a.t.mean())
        assert st["declines"] == (st["rise"] > 1e-9) and st["harm"] == (st["et_inf"] > st["et_1"])
        assert 0 < st["percentile"] <= 1 and -1 <= st["spearman"] <= 1
        cur = ev.current(a)
        assert cur["et"] == pytest.approx(a.et[8]) and cur["vs_min"] >= -1e-12


def test_everything_is_deterministic():
    a1, a2 = ev.analyse(ev.Settings(6, 1, 4, 50, 0, 1, 10)), ev.analyse(ev.Settings(6, 1, 4, 50, 0, 1, 10))
    assert (a1.p == a2.p).all() and (a1.et == a2.et).all() and ev.summary(a1) == ev.summary(a2)
    assert ev.curve_rows(a1) == ev.curve_rows(a2)
