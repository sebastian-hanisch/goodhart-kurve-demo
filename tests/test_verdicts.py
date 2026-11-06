"""Verdikte: Art und Wortlaut in den Fällen, die sie unterscheiden (DEMO-PLAYBOOK §6): jede Zahl im Text kommt aus der Rechnung."""

import gdh_constants as C
import gdh_evaluation as ev

(P_NOISE, P_FLUCH, P_CORR, P_HARM, P_HIDDEN, P_NOW, P_MAX, P_N3) = list(C.PRESETS)


def _all(name):
    a = ev.analyse(ev.Settings(**C.PRESETS[name]))
    return a, ev.summary(a), ev.current(a)


def test_curve_verdict_distinguishes_rise_harm_and_no_rise():
    a, st, cur = _all(P_NOISE)
    kind, text = ev.verdict_curve(st)
    assert kind == "warning" and text == "Der wahre Wert ist bei k = **2^13** am besten (E[T] = 250,0, 39,3 % besser als bei k = 1) und **steigt danach bis k = ∞ um 10,3 %** auf 275,8."
    a, st, cur = _all(P_HARM)
    kind, text = ev.verdict_curve(st)
    assert kind == "warning" and text.startswith("**Optimieren schadet:** der wahre Wert ist bei k = 2^11 am besten (E[T] = 364,1)") and "um **16,1 %**" in text and "schlechter als ein Zufallsplan (E[T] = 400,3)" in text
    a, st, cur = _all(P_NOW)
    assert "bei k = 1 am besten (E[T] = 1198,6)" in ev.verdict_curve(st)[1]
    a, st, cur = _all(P_MAX)
    kind, text = ev.verdict_curve(st)
    assert kind == "info" and text.startswith("Hier wird der wahre Wert mit jeder Stärke besser: das Minimum liegt bei k = ∞ (E[T] = 44,0, 52,5 % besser als bei k = 1)")
    a, st, cur = _all(P_N3)
    assert "bei k = **4** am besten (E[T] = 264,3, 11,7 % besser als bei k = 1)" in ev.verdict_curve(st)[1] and "um 12,1 %** auf 296,3" in ev.verdict_curve(st)[1]


def test_current_verdict_compares_with_the_best_strength():
    a, st, cur = _all(P_NOISE)
    kind, text = ev.verdict_current(cur, st)
    assert kind == "success" and "Bei k = 2^13 verspricht das Ersatzziel E[P] = -107,4 und es gilt E[T] = 250,0: die Wirklichkeit liegt **143,0 % über** dem Versprechen. Das ist die beste Stärke der Kurve." == text
    a, st, cur = _all(P_FLUCH)
    kind, text = ev.verdict_current(cur, st)
    assert kind == "warning" and "Bei k = ∞ verspricht" in text and "Der beste wahre Wert liegt bei k = 2^15 (E[T] = 277,1); hier ist er 5,2 % schlechter." in text
    a, st, cur = _all(P_MAX)
    kind, text = ev.verdict_current(cur, st)
    assert kind == "success" and "verschiedene" not in text and "ein Versprechen in derselben Einheit gibt es nicht" in text


def test_gap_verdict_has_the_promise_the_reality_and_the_best_plan():
    a, st, cur = _all(P_FLUCH)
    kind, text = ev.verdict_gap(st)
    assert kind == "warning" and text == ("Am P-Optimum verspricht das Ersatzziel P = -49,9; gilt T = 291,5: die Lücke ist **117,1 %** (optimistisch). Der wahre beste Plan hat T = 125,3; das P-Optimum hat T = 291,5.")
    a, st, cur = _all(P_MAX)
    assert ev.verdict_gap(st)[0] == "info" and "verschiedene Einheiten" in ev.verdict_gap(st)[1]
    a = ev.analyse(ev.Settings(6, 0, 100000, 0, 0, 1, 21))
    kind, text = ev.verdict_gap(ev.summary(a))
    assert kind == "info" and "ist das P-Optimum." in text and "**0,0 %**" in text


def test_fresh_verdict_uses_the_fixed_seed_draws():
    a, st, cur = _all(P_NOISE)
    f = ev.fresh_check(a)
    kind, text = ev.verdict_fresh(f)
    assert kind == "info" and text.startswith("Das P-Optimum wurde 200-mal frisch gemessen") and "wahrer Wert 275,8, gemessenes Versprechen -153,1" in text
    assert f["fresh_mean"] == ev.fresh_check(a)["fresh_mean"] and abs(f["fresh_mean"] - f["true"]) < 4 * f["fresh_sd"] / 200 ** 0.5


def test_models_verdict_names_all_three_models():
    a, st, cur = _all(P_CORR)
    text = ev.verdict_models(ev.model_compare(a))[1]
    assert "Rauschen: Minimum bei k = " in text and "Verdeckte Kosten: Minimum bei k = 2^11, danach +17,2 %, Spearman 0,85" in text and "Summe statt Maximum: Minimum bei k = ∞, kein Anstieg" in text


def test_sweep_verdicts_carry_the_phase_zero_numbers():
    noise = ev.noise_sweep()
    assert [noise[s]["declines"] for s in C.SWEEP_SIGMAS] == [7, 13, 12, 16, 12] and [noise[s]["harm"] for s in C.SWEEP_SIGMAS] == [0, 0, 0, 1, 3]
    text = ev.verdict_noise_sweep(noise)[1]
    assert "σ = 5: 7 von 20 (Anstieg Median 0,0 %, Maximum 6,6 %; Optimum schlechter als Zufallsplan 0; Lücke Median 8 %)" in text and "σ = 100: 12 von 20" in text
    hidden = ev.hidden_sweep()
    assert [hidden[(1, r)]["declines"] for r in (50, 0, -50, -90)] == [11, 17, 17, 16] and [hidden[(2, r)]["declines"] for r in (50, 0, -50, -90)] == [13, 17, 17, 20]
    assert [hidden[(2, r)]["harm"] for r in (50, 0, -50, -90)] == [0, 4, 11, 20]
    assert "w = 2, r = -0,9: 20 von 20" in ev.verdict_hidden_sweep(hidden)[1]
    mx = ev.max_sweep()
    assert (mx["declines"], mx["harm"]) == (8, 0) and "Anstieg nach dem Minimum in 8 von 20 Instanzen" in ev.verdict_max_sweep(mx)[1]
    sp = ev.spearman_sweep()
    text = ev.verdict_spearman_sweep(sp, hidden, noise)[1]
    assert "Rauschen, σ = 25: Spearman Median 0,78" in text and "verdeckt, w = 2, r = −0,9: Spearman Median -0,62" in text and "in 12 von 20 Instanzen (Rauschen, σ = 25) und in 11 von 20" in text
