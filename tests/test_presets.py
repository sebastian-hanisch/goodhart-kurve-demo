"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und was jedes Preset zeigen soll."""

import gdh_constants as C
import gdh_evaluation as ev
import gdh_presets as P

(P_NOISE, P_FLUCH, P_CORR, P_HARM, P_HIDDEN, P_NOW, P_MAX, P_N3) = list(C.PRESETS)


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["model"] < len(C.MODELS) and 0 <= preset["seed"] <= C.SEED_MAX
        assert C.SIGMA_MIN <= preset["sigma"] <= C.SIGMA_MAX and preset["sigma"] % C.SIGMA_STEP == 0
        assert C.CORR_MIN <= preset["corr"] <= C.CORR_MAX and preset["corr"] % C.CORR_STEP == 0
        assert C.W_MIN <= preset["w"] <= C.W_MAX and C.K_EXP_MIN <= preset["k_exp"] <= C.K_EXP_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[P_NOISE]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_non_default_preset_equals_the_default_settings():
    """Lehre aus Stück 4: ein Preset, das den Voreinstellungen gleicht, wäre nicht von „nichts geklickt“ zu unterscheiden."""
    for name, preset in C.PRESETS.items():
        if name != P_NOISE:
            assert ev.Settings(**preset) != ev.Settings(), name


def _all(name):
    a = ev.analyse(ev.Settings(**C.PRESETS[name]))
    return a, ev.summary(a)


def test_noise_preset_has_the_minimum_at_two_to_the_thirteen_and_the_documented_numbers():
    a, st = _all(P_NOISE)
    assert (st["e"], st["declines"], round(st["min"], 1), round(st["et_inf"], 1), ev.pct(st["gain"]), ev.pct(st["rise"])) == (13, True, 250.0, 275.8, "39,3 %", "10,3 %")


def test_fluch_preset_promises_a_negative_cost_and_is_off_by_a_hundred_percent():
    a, st = _all(P_FLUCH)
    assert st["p_opt"] < 0 < st["t_of_p_opt"] and ev.pct(st["gap_inf"], 0) == "117 %" and round(st["t_of_p_opt"], 1) == 291.5 and ev.de(st["p_opt"]) == "-49,9"


def test_correlation_preset_has_a_high_rank_correlation_and_still_a_rise():
    a, st = _all(P_CORR)
    assert round(st["spearman"], 2) == 0.85 and st["declines"] and ev.pct(st["rise"]) == "17,2 %" and st["e"] == 11


def test_harm_preset_has_a_worse_optimum_than_a_random_plan():
    a, st = _all(P_HARM)
    assert st["harm"] and st["et_inf"] > st["et_1"] and round(st["et_inf"], 1) == 422.6 and round(st["et_1"], 1) == 400.3 and ev.pct(st["percentile"], 0) == "61 %"


def test_hidden_cost_presets_show_almost_no_gain_and_an_immediate_loss():
    a, st = _all(P_HIDDEN)
    assert (st["e"], ev.pct(st["gain"]), ev.pct(st["rise"]), ev.pct(1 - st["percentile"], 0)) == (3, "1,2 %", "19,7 %", "6 %") and st["harm"]
    a, st = _all(P_NOW)
    assert (st["e"], st["gain"], st["harm"], round(st["spearman"], 2)) == (0, 0.0, True, -0.59) and ev.pct(st["percentile"], 0) == "96 %"


def test_max_preset_improves_with_every_strength():
    a, st = _all(P_MAX)
    assert not st["declines"] and st["e"] == 21 and ev.pct(st["gain"]) == "52,5 %" and not ev.comparable("max")


def test_smallest_example_has_six_plans_and_the_documented_numbers():
    a, st = _all(P_N3)
    assert st["n_plans"] == 6 and st["e"] == 2 and round(st["min"], 1) == 264.3 and round(st["et_inf"], 1) == 296.3 and ev.pct(st["rise"]) == "12,1 %"
