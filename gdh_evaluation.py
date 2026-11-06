"""Kennzahlen, Verdikt-Logik und Sweeps. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Gefragt wird: Wie verhält sich das wahre Ziel T, wenn man das Ersatzziel P stärker optimiert (Best-of-k, k bis unendlich)? Wo liegt das Minimum, wie stark steigt T danach wieder, wie groß ist die Lücke
zwischen Versprechen (P) und Wirklichkeit (T), und schützt eine positive Korrelation davor?"""

from dataclasses import dataclass

import numpy as np

import gdh_algorithm as A
import gdh_constants as C
import gdh_scenario as S


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma; kein „-0,0“."""
    text = f"{x:.{digits}f}"
    if float(text) == 0.0:
        text = f"{0.0:.{digits}f}"
    return text.replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    """Anteil als Prozent: 0,05 -> „5,0 %“."""
    return de(x * 100.0, digits) + " %"


def k_text(e: int) -> str:
    """Optimierungsstärke k = 2^e; der größte Exponent steht für unendlich."""
    if e >= C.K_INF:
        return "∞"
    return str(2 ** e) if e <= 3 else f"2^{e}"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    model: int = C.DEFAULT_MODEL
    seed: int = C.DEFAULT_SEED
    sigma: int = C.DEFAULT_SIGMA
    corr: int = C.DEFAULT_CORR
    w: int = C.DEFAULT_W
    k_exp: int = C.DEFAULT_K_EXP

    @property
    def name(self) -> str:
        return C.MODELS[self.model]


@dataclass
class Analysis:
    settings: Settings
    p: np.ndarray              # Ersatzziel je Plan
    t: np.ndarray              # wahres Ziel je Plan
    mats: dict
    et: np.ndarray             # E[T] je k (Gitter A.KS_ALL)
    ep: np.ndarray             # E[P] je k


def _build(name: str, n: int, seed: int, sigma, corr, w):
    return S.make_model(name, n, seed, sigma, corr / 100.0, w)


def analyse(settings: Settings) -> Analysis:
    p, t, mats = _build(settings.name, settings.n, settings.seed, settings.sigma, settings.corr, settings.w)
    et, ep = A.expected_curve(p, t)
    return Analysis(settings, p, t, mats, et, ep)


# --- Experimente auf einer Instanz ---------------------------------------------------------------------------------------------------------

def comparable(name: str) -> bool:
    """P und T haben dieselbe Einheit (Kosten)? Beim Maß „Summe gegen Maximum“ nicht: dort gibt es keine Lücke zwischen Versprechen und Wirklichkeit."""
    return name != "max"


def curve_rows(a: Analysis) -> list[dict]:
    """E[T], E[P] und die Lücke (T - P) / T je Optimierungsstärke (ohne Lücke beim Maß „Summe gegen Maximum“)."""
    rows = []
    cmp_ = comparable(a.settings.name)
    for e, k, et, ep in zip(range(C.K_EXP_MIN, C.K_EXP_MAX + 1), A.KS_ALL, a.et, a.ep):
        rows.append({"e": e, "k": k, "et": float(et), "ep": float(ep), "gap": (float((et - ep) / et) if et else 0.0) if cmp_ else None})
    return rows


def summary(a: Analysis) -> dict:
    """Kurve und Kennzahlen: Minimum, Anstieg, Gewinn, Lücke am Optimum, Perzentil und Rangkorrelation."""
    st = A.curve_stats(a.et)
    i_p = int(np.argmin(a.p))
    i_t = int(np.argmin(a.t))
    return {**st, "n_plans": len(a.p), "et_1": float(a.et[0]), "et_inf": float(a.et[-1]), "ep_inf": float(a.ep[-1]), "gap_inf": (float((a.et[-1] - a.ep[-1]) / a.et[-1]) if a.et[-1] else 0.0) if comparable(a.settings.name) else None,
            "percentile": A.percentile_of_optimum(a.p, a.t), "spearman": A.rank_correlation(a.p, a.t), "t_best": float(a.t[i_t]), "t_of_p_opt": float(a.t[i_p]), "p_opt": float(a.p[i_p]),
            "p_opt_is_t_best": bool(i_p == i_t), "idx_p": i_p, "idx_t": i_t}


def current(a: Analysis) -> dict:
    """Die Stelle der Kurve, die der Regler k wählt."""
    e = a.settings.k_exp
    i = e - C.K_EXP_MIN
    et, ep = float(a.et[i]), float(a.ep[i])
    return {"e": e, "k": A.KS_ALL[i], "et": et, "ep": ep, "gap": ((et - ep) / et if et else 0.0) if comparable(a.settings.name) else None, "vs_1": (et - a.et[0]) / a.et[0] if a.et[0] else 0.0, "vs_min": (et - a.et.min()) / a.et.min() if a.et.min() else 0.0}


def fresh_check(a: Analysis) -> dict | None:
    """Rauschen: das P-Optimum frisch gemessen (FRESH_DRAWS unabhängige zweite Messfehler): der Mittelwert liegt bei T, das Versprechen P nicht. Sonst None."""
    if a.settings.name != "noise":
        return None
    n, s = a.settings.n, a.settings.sigma
    plan = S.all_plans(n)[int(np.argmin(a.p))].astype(int)
    rng = np.random.default_rng(a.settings.seed + 7919)
    arr = a.mats["A"]
    fresh = []
    for _ in range(C.FRESH_DRAWS):
        noise = rng.normal(0.0, s, (n, n))
        fresh.append(float((arr + noise)[np.arange(n), plan].sum()))
    return {"claimed": float(a.p.min()), "true": float(a.t[int(np.argmin(a.p))]), "fresh_mean": float(np.mean(fresh)), "fresh_sd": float(np.std(fresh)), "draws": C.FRESH_DRAWS}


def model_compare(a: Analysis) -> list[dict]:
    """Dieselbe Größe und derselbe Seed mit den drei Modellen (mit den eingestellten Parametern)."""
    s = a.settings
    rows = []
    for name in C.MODELS:
        p, t, _ = _build(name, s.n, s.seed, s.sigma, s.corr, s.w)
        et, _ = A.expected_curve(p, t)
        st = A.curve_stats(et)
        rows.append({"model": name, "e": st["e"], "rise": st["rise"], "gain": st["gain"], "declines": st["declines"], "harm": st["harm"], "percentile": A.percentile_of_optimum(p, t), "spearman": A.rank_correlation(p, t)})
    return rows


# --- Sweeps über feste Instanzen -----------------------------------------------------------------------------------------------------------

def _q3(vals) -> tuple[float, float, float]:
    v = np.asarray(vals, dtype=float)
    return float(v.min()), float(np.median(v)), float(v.max())


def _stats_over(maker, seeds) -> dict:
    declines = harm = 0
    rises, gains, gaps, percs, ks = [], [], [], [], []
    for s in seeds:
        p, t, _ = maker(s)
        et, ep = A.expected_curve(p, t)
        st = A.curve_stats(et)
        declines += st["declines"]
        harm += st["harm"]
        rises.append(st["rise"])
        gains.append(st["gain"])
        gaps.append((et[-1] - ep[-1]) / et[-1])
        percs.append(A.percentile_of_optimum(p, t))
        ks.append(2 ** C.K_INF if st["k"] is None else st["k"])
    return {"declines": int(declines), "harm": int(harm), "rise": _q3(rises), "gain": _q3(gains), "gap": _q3(gaps), "perc": _q3(percs), "k": _q3(ks), "seeds": len(list(seeds))}


def noise_sweep(sigmas=C.SWEEP_SIGMAS, n: int = C.SWEEP_N, seeds=C.SWEEP_SEEDS) -> dict:
    """Rauschen je σ: Instanzen mit Anstieg, Optimum schlechter als ein Zufallsplan, Anstieg, Gewinn, Lücke, Perzentil."""
    return {sg: _stats_over(lambda s, sg=sg: S.make_noise(n, s, sg), seeds) for sg in sigmas}


def hidden_sweep(ws=C.SWEEP_WS, corrs=C.SWEEP_CORRS, n: int = C.SWEEP_N, seeds=C.SWEEP_SEEDS) -> dict:
    """Verdeckte Kosten je (w, r in Prozent)."""
    return {(w, r): _stats_over(lambda s, w=w, r=r: S.make_hidden(n, s, r / 100.0, w), seeds) for w in ws for r in corrs}


def max_sweep(n: int = C.SWEEP_N, seeds=C.SWEEP_SEEDS) -> dict:
    """Summe als Ersatz für das Maximum."""
    return _stats_over(lambda s: S.make_max(n, s), seeds)


def spearman_sweep(n: int = C.SWEEP_N, seeds=C.SPEARMAN_SEEDS) -> dict:
    """Rangkorrelation von P und T über alle Pläne (Min/Median/Max über die Instanzen) für typische Einstellungen."""
    cases = {"Rauschen, σ = 25": lambda s: S.make_noise(n, s, 25), "verdeckt, w = 1, r = +0,5": lambda s: S.make_hidden(n, s, 0.5, 1), "verdeckt, w = 1, r = −0,5": lambda s: S.make_hidden(n, s, -0.5, 1),
             "verdeckt, w = 2, r = −0,9": lambda s: S.make_hidden(n, s, -0.9, 2), "Summe gegen Maximum": lambda s: S.make_max(n, s)}
    out = {}
    for name, maker in cases.items():
        out[name] = _q3([A.rank_correlation(*maker(s)[:2]) for s in seeds])
    return out


# --- Verdikte ------------------------------------------------------------------------------------------------------------------------------

def verdict_curve(st: dict) -> tuple[str, str]:
    """Experiment Kurve: wo ist der wahre Wert am besten, und was passiert danach?"""
    if not st["declines"]:
        return "info", (f"Hier wird der wahre Wert mit jeder Stärke besser: das Minimum liegt bei k = ∞ (E[T] = {de(st['min'])}, {pct(st['gain'])} besser als bei k = 1). "
                        f"Das P-Optimum ist bei T besser als {pct(1 - st['percentile'])} der Pläne.")
    if st["harm"]:
        return "warning", (f"**Optimieren schadet:** der wahre Wert ist bei k = {k_text(st['e'])} am besten (E[T] = {de(st['min'])}) und steigt danach bis k = ∞ um **{pct(st['rise'])}**; "
                           f"das P-Optimum (E[T] = {de(st['et_inf'])}) ist schlechter als ein Zufallsplan (E[T] = {de(st['et_1'])}).")
    return "warning", (f"Der wahre Wert ist bei k = **{k_text(st['e'])}** am besten (E[T] = {de(st['min'])}, {pct(st['gain'])} besser als bei k = 1) und **steigt danach bis k = ∞ um {pct(st['rise'])}** "
                       f"auf {de(st['et_inf'])}.")


def verdict_current(cur: dict, st: dict) -> tuple[str, str]:
    """Die Stelle des Reglers: Versprechen gegen Wirklichkeit."""
    k = k_text(cur["e"])
    if cur["gap"] is None:
        base = f"Bei k = {k} gilt E[T] = {de(cur['et'])} (das Ersatzziel ist eine Summe, das wahre Ziel ein Maximum: ein Versprechen in derselben Einheit gibt es nicht). "
    else:
        base = (f"Bei k = {k} verspricht das Ersatzziel E[P] = {de(cur['ep'])} und es gilt E[T] = {de(cur['et'])}: die Wirklichkeit liegt **{pct(abs(cur['gap']))} "
                f"{'über' if cur['gap'] >= 0 else 'unter'}** dem Versprechen. ")
    if cur["vs_min"] <= 1e-12:
        return "success", base + "Das ist die beste Stärke der Kurve."
    return ("warning" if cur["vs_min"] > 0.005 else "info"), base + f"Der beste wahre Wert liegt bei k = {k_text(st['e'])} (E[T] = {de(st['min'])}); hier ist er {pct(cur['vs_min'])} schlechter."


def verdict_gap(st: dict) -> tuple[str, str]:
    """Experiment Fluch des Gewinners: das Versprechen am Optimum."""
    if st["gap_inf"] is None:
        return "info", "Beim Maß „Summe gegen Maximum“ haben Ersatzziel und wahres Ziel verschiedene Einheiten; ein Versprechen und seine Lücke gibt es dort nicht."
    t_best = f" Der wahre beste Plan hat T = {de(st['t_best'])}" + (" und ist das P-Optimum." if st["p_opt_is_t_best"] else f"; das P-Optimum hat T = {de(st['t_of_p_opt'])}.")
    return "warning" if abs(st["gap_inf"]) > 0.05 else "info", (f"Am P-Optimum verspricht das Ersatzziel P = {de(st['p_opt'])}; gilt T = {de(st['t_of_p_opt'])}: die Lücke ist **{pct(abs(st['gap_inf']))}** "
                                                              f"({'optimistisch' if st['gap_inf'] > 0 else 'pessimistisch'}).{t_best}")


def verdict_fresh(f: dict) -> tuple[str, str]:
    """Frische Messung des P-Optimums."""
    return "info", (f"Das P-Optimum wurde {f['draws']}-mal frisch gemessen (unabhängiger zweiter Messfehler): Mittelwert **{de(f['fresh_mean'])}**, wahrer Wert {de(f['true'])}, gemessenes Versprechen {de(f['claimed'])}. "
                    f"Auf frischen Daten verschwindet die Lücke im Mittel; auf den Daten, die ausgewählt haben, nicht.")


def verdict_models(rows: list[dict]) -> tuple[str, str]:
    """Experiment Welche Art: dieselbe Instanz, drei Modelle."""
    parts = []
    for r in rows:
        k = k_text(r["e"])
        parts.append(f"{C.MODEL_SHORT[r['model']]}: Minimum bei k = {k}, " + (f"danach +{pct(r['rise'])}" if r["declines"] else "kein Anstieg") + f", Spearman {de(r['spearman'], 2)}")
    return "info", "; ".join(parts) + "."


def verdict_noise_sweep(res: dict) -> tuple[str, str]:
    cells = [f"σ = {sg}: {r['declines']} von {r['seeds']} (Anstieg Median {pct(r['rise'][1])}, Maximum {pct(r['rise'][2])}; Optimum schlechter als Zufallsplan {r['harm']}; Lücke Median {pct(r['gap'][1], 0)})" for sg, r in res.items()]
    return "info", f"Rauschen, n = {C.SWEEP_N}, Instanzen mit Anstieg nach dem Minimum, je {len(C.SWEEP_SEEDS)} feste Instanzen: " + "; ".join(cells) + "."


def verdict_hidden_sweep(res: dict) -> tuple[str, str]:
    cells = [f"w = {w}, r = {de(r / 100, 1)}: {x['declines']} von {x['seeds']} (Anstieg Median {pct(x['rise'][1])}, Maximum {pct(x['rise'][2])}; Optimum schlechter als Zufallsplan {x['harm']}; Gewinn Median {pct(x['gain'][1])})"
             for (w, r), x in res.items()]
    return "info", f"Verdeckte Kosten, n = {C.SWEEP_N}, Instanzen mit Anstieg nach dem Minimum, je {len(C.SWEEP_SEEDS)} feste Instanzen: " + "; ".join(cells) + "."


def verdict_max_sweep(r: dict) -> tuple[str, str]:
    return "info", (f"Summe gegen Maximum, n = {C.SWEEP_N}: Anstieg nach dem Minimum in {r['declines']} von {r['seeds']} Instanzen (Median {pct(r['rise'][1])}, Maximum {pct(r['rise'][2])}); "
                    f"Optimum schlechter als Zufallsplan {r['harm']}; Perzentil des P-Optimums bei T Median {de(r['perc'][1] * 100)}, Maximum {de(r['perc'][2] * 100)}.")


def verdict_spearman_sweep(res: dict, hid: dict, noi: dict) -> tuple[str, str]:
    parts = [f"{name}: Spearman Median {de(v[1], 2)}" for name, v in res.items()]
    return "info", (f"Rangkorrelation von P und T über alle Pläne (je {len(C.SPEARMAN_SEEDS)} Instanzen): " + "; ".join(parts) + f". Trotz Korrelation steigt T nach dem Minimum in {noi[25]['declines']} von {noi[25]['seeds']} Instanzen "
                    f"(Rauschen, σ = 25) und in {hid[(1, 50)]['declines']} von {hid[(1, 50)]['seeds']} (verdeckt, w = 1, r = +0,5).")
