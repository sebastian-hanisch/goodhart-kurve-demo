"""Experimente der App: jedes Preset, jedes Modell, jede Stärke, jede Größe und alle Schalter laufen ohne Fehler."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import gdh_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(m.value for kind in ("success", "info", "warning") for m in getattr(at, kind))


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_shows_a_verdict(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, (name, [str(e) for e in at.exception])
    assert "wahre Wert" in _texts(at)


def test_default_preset_shows_the_rise_after_the_minimum():
    assert "steigt danach bis k = ∞ um 10,3 %" in _texts(_app())


@pytest.mark.parametrize("model", range(len(C.MODELS)))
def test_every_model_runs_and_is_named(model):
    at = _app()
    at.sidebar.selectbox(key="model_select").set_value(model).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert C.MODEL_SHORT[C.MODELS[model]] in " ".join(m.value for m in at.markdown)


@pytest.mark.parametrize("k_exp", [C.K_EXP_MIN, 1, 8, 20, C.K_EXP_MAX])
def test_every_strength_runs(k_exp):
    at = _app()
    at.sidebar.slider(key="k_exp_slider").set_value(k_exp).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "Bei k = " in _texts(at)


@pytest.mark.parametrize("key,value", [("sigma_slider", 0), ("sigma_slider", 100), ("corr_slider", -90), ("corr_slider", 90), ("w_slider", 1), ("w_slider", 4)])
def test_every_parameter_extreme_runs(key, value):
    at = _app()
    at.sidebar.selectbox(key="model_select").set_value(1).run()
    at.sidebar.slider(key=key).set_value(value).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("n", [3, 5, 8])
def test_sizes_run(n):
    at = _app()
    at.sidebar.slider(key="n_slider").set_value(n).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "wahre Wert" in _texts(at)


def test_the_sweeps_run_when_switched_on():
    at = _app()
    for key in ("sweep_noise", "sweep_hidden", "sweep_corr"):
        at.toggle(key=key).set_value(True).run()
        assert not at.exception, (key, [str(e) for e in at.exception])
    text = _texts(at)
    assert "Rauschen, n = 8" in text and "Verdeckte Kosten, n = 8" in text and "Summe gegen Maximum, n = 8" in text and "Rangkorrelation von P und T" in text
