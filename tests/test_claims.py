"""Jede Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4). Aufzählung, exakte Ordnungsstatistik und feste Instanzerzeugung sind deterministisch."""

from pathlib import Path

import pytest

import gdh_constants as C
import gdh_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
(P_NOISE, P_FLUCH, P_HARM, P_CORR, P_HIDDEN, P_NOW, P_MAX, P_N3) = (list(C.PRESETS)[i] for i in (0, 1, 3, 2, 4, 5, 6, 7))


def _claim(text):
    assert text in README, text


def _slash(values, fmt):
    return " / ".join(fmt(v) for v in values)


def _preset(name):
    a = ev.analyse(ev.Settings(**C.PRESETS[name]))
    return a, ev.summary(a)


@pytest.fixture(scope="module")
def noise():
    return ev.noise_sweep()


@pytest.fixture(scope="module")
def hidden():
    return ev.hidden_sweep()


@pytest.fixture(scope="module")
def maxsw():
    return ev.max_sweep()


@pytest.fixture(scope="module")
def spearman():
    return ev.spearman_sweep()


def test_sweep_instances_are_the_documented_ones():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100020)) and C.SWEEP_N == 8 and C.SWEEP_SIGMAS == (5, 10, 25, 50, 100) and C.SWEEP_CORRS == (50, 0, -50, -90)
    _claim("Seeds 100000 bis 100019")


def test_noise_claims(noise):
    sg = C.SWEEP_SIGMAS
    assert [noise[s]["declines"] for s in sg] == [7, 13, 12, 16, 12] and [noise[s]["harm"] for s in sg] == [0, 0, 0, 1, 3]
    _claim("**7 / 13 / 12 / 16 / 12** von 20")
    _claim("Anstieg Median " + _slash([noise[s]["rise"][1] for s in sg], ev.pct) + ", Maximum " + _slash([noise[s]["rise"][2] for s in sg], ev.pct))
    _claim("**0 / 0 / 0 / 1 / 3** von 20")
    _claim(_slash([noise[s]["gain"][1] for s in sg], ev.pct))
    _claim(_slash([noise[s]["gap"][1] for s in sg], ev.pct))
    _claim(_slash([noise[s]["perc"][1] for s in sg], ev.pct))
    assert _slash([noise[s]["gain"][1] for s in sg], ev.pct) == "66,5 % / 60,7 % / 54,7 % / 39,3 % / 32,7 %" and _slash([noise[s]["gap"][1] for s in sg], ev.pct) == "8,2 % / 30,1 % / 84,4 % / 169,9 % / 303,3 %"
    assert _slash([noise[s]["perc"][1] for s in sg], ev.pct) == "0,0 % / 0,0 % / 0,1 % / 3,3 % / 5,6 %"


def test_hidden_claims(hidden):
    cs = C.SWEEP_CORRS
    for w, harm, counts, gains in ((1, [0, 0, 1, 5], [11, 17, 17, 16], "45,7 % / 31,8 % / 16,5 % / 3,5 %"), (2, [0, 4, 11, 20], [13, 17, 17, 20], "41,2 % / 20,7 % / 1,3 % / 0,0 %")):
        assert [hidden[(w, r)]["declines"] for r in cs] == counts and [hidden[(w, r)]["harm"] for r in cs] == harm
        assert _slash([hidden[(w, r)]["gain"][1] for r in cs], ev.pct) == gains
        _claim("Anstieg in **" + " / ".join(map(str, counts)) + "** von 20" if w == 2 else "**" + " / ".join(map(str, counts)) + "** von 20")
        _claim(f"Optimum schlechter als Zufallsplan in **{' / '.join(map(str, harm))}**")
        _claim("Gewinn Median " + gains if w == 1 else "Gewinn Median " + gains)
        _claim("Median " + _slash([hidden[(w, r)]["rise"][1] for r in cs], ev.pct).replace("20,5 %", "**20,5 %**") if w == 2 else "Anstieg Median " + _slash([hidden[(w, r)]["rise"][1] for r in cs], ev.pct))
        _claim("Maximum " + _slash([hidden[(w, r)]["rise"][2] for r in cs], ev.pct))
    assert _slash([hidden[(2, r)]["k"][1] for r in cs], lambda v: f"{int(v):,}".replace(",", " ")) == "49 152 / 8 192 / 12 / 1"
    _claim("Minimum der Kurve im Median bei k = 49 152 / 8 192 / 12 / 1")
    assert ev.pct(hidden[(2, -90)]["perc"][1]) == "99,8 %"
    _claim("Perzentil des P-Optimums 99,8 %")


def test_max_claims(maxsw):
    assert (maxsw["declines"], maxsw["harm"], ev.pct(maxsw["rise"][1]), ev.pct(maxsw["rise"][2]), ev.pct(maxsw["gain"][1]), ev.pct(maxsw["perc"][1]), ev.pct(maxsw["perc"][2])) == (8, 0, "0,0 %", "7,7 %", "58,7 %", "0,0 %", "1,3 %")
    _claim("Anstieg in **8** von 20 (Median 0,0 %, Maximum 7,7 %), Optimum schlechter als Zufallsplan in **0**; Gewinn Median 58,7 %; Perzentil des P-Optimums bei T Median 0,0 %, Maximum 1,3 %")


def test_spearman_claims(spearman, hidden, noise):
    vals = [round(v[1], 2) for v in spearman.values()]
    assert vals == [0.78, 0.84, 0.5, -0.62, 0.49]
    _claim("Rauschen σ = 25: **0,78**; verdeckt w = 1, r = +0,5: **0,84**; r = −0,5: **0,50**; w = 2, r = −0,9: **−0,62**; Summe gegen Maximum: **0,49**")
    assert (noise[25]["declines"], hidden[(1, 50)]["declines"]) == (12, 11)
    _claim("Trotz 0,78 steigt T nach dem Minimum in **12** von 20 Instanzen (Rauschen σ = 25), trotz 0,84 in **11** von 20 (verdeckt, w = 1, r = +0,5)")


def test_preset_claims():
    a, st = _preset(P_NOISE)
    assert (st["e"], ev.de(st["min"]), ev.pct(st["gain"]), ev.pct(st["rise"]), ev.de(st["et_inf"]), ev.de(st["p_opt"]), ev.pct(st["gap_inf"]), ev.de(st["t_best"])) == (13, "250,0", "39,3 %", "10,3 %", "275,8", "-153,1", "155,5 %", "148,8")
    _claim("Minimum bei k = 2¹³ mit E[T] = **250,0** (**39,3 %** besser als bei k = 1), danach Anstieg um **10,3 %** auf **275,8**; am Optimum verspricht P = **−153,1**, es gilt T = 275,8 (Lücke **155,5 %**), der wahre beste Plan hat T = **148,8**")
    a, st = _preset(P_FLUCH)
    assert (ev.de(st["p_opt"]), ev.de(st["t_of_p_opt"]), ev.pct(st["gap_inf"]), st["e"], ev.de(st["min"]), ev.pct(st["rise"])) == ("-49,9", "291,5", "117,1 %", 15, "277,1", "5,2 %")
    _claim("am Optimum verspricht P = **−49,9**, es gilt T = **291,5**: Lücke **117,1 %**; Minimum bei k = 2¹⁵ mit 277,1, Anstieg **5,2 %**")
    a, st = _preset(P_HARM)
    assert (ev.de(st["et_inf"]), ev.de(st["et_1"]), st["e"], ev.de(st["min"]), ev.pct(st["rise"]), ev.pct(st["percentile"])) == ("422,6", "400,3", 11, "364,1", "16,1 %", "61,2 %")
    _claim("E[T] am Optimum **422,6**, bei einem Zufallsplan **400,3**; Minimum bei k = 2¹¹ mit **364,1**, Anstieg **16,1 %**; schlechter als **61,2 %** der Pläne")
    a, st = _preset(P_CORR)
    assert (round(st["spearman"], 2), st["e"], ev.de(st["min"]), ev.pct(st["rise"]), ev.de(st["et_inf"])) == (0.85, 11, "476,1", "17,2 %", "557,9")
    _claim("Spearman **0,85**, Minimum bei k = 2¹¹ mit **476,1**, Anstieg **17,2 %** auf **557,9**")
    a, st = _preset(P_HIDDEN)
    assert (ev.pct(st["gain"]), st["e"], ev.pct(st["rise"]), ev.pct(1 - st["percentile"])) == ("1,2 %", 3, "19,7 %", "5,8 %")
    _claim("Gewinn nur **1,2 %** (Minimum bei k = 8), danach Anstieg um **19,7 %**; das Optimum ist bei T besser als nur **5,8 %** der Pläne")
    a, st = _preset(P_NOW)
    assert (st["e"], ev.de(st["min"]), ev.de(st["et_inf"]), ev.pct(st["rise"]), round(st["spearman"], 2)) == (0, "1198,6", "1355,5", "13,1 %", -0.59)
    _claim("Minimum bei **k = 1** (E[T] = **1198,6**), das Optimum **1355,5** (**13,1 %** mehr), Spearman **−0,59**")
    a, st = _preset(P_MAX)
    assert (ev.de(st["et_1"]), ev.de(st["et_inf"]), ev.pct(st["gain"]), st["declines"]) == ("92,6", "44,0", "52,5 %", False)
    _claim("E[T] fällt von **92,6** (k = 1) auf **44,0** (k = ∞): **52,5 %** Gewinn, kein Anstieg")
    a, st = _preset(P_N3)
    assert (st["e"], ev.de(st["min"]), ev.pct(st["gain"]), ev.de(st["et_inf"]), ev.pct(st["rise"]), ev.pct(st["gap_inf"])) == (2, "264,3", "11,7 %", "296,3", "12,1 %", "69,6 %")
    _claim("Minimum bei k = **4** mit **264,3** (**11,7 %** besser als k = 1), am Optimum **296,3** (**12,1 %** mehr), Lücke **69,6 %**")


def test_hand_example_numbers_in_the_readme_text():
    _claim("(62/3, 341/18, 11753/648, 20), das Minimum bei k = 4, Lücke 65 %")
