"""Kern der Demo (numpy, scipy): die Wirkung einer stärkeren Optimierung des Ersatzziels P auf das wahre Ziel T.

Optimierungsstärke k heißt: unter k zufällig und gleichverteilt (mit Zurücklegen) gezogenen Plänen wird der mit dem kleinsten P gewählt (Best-of-k). k = unendlich ist das Optimum von P.
Der Erwartungswert von T (und von P) über diese Wahl ist EXAKT berechenbar: sortiert man die N Pläne nach P aufsteigend (stabil: bei Gleichstand gilt die Reihenfolge der Aufzählung),
wird der Plan auf Rang r mit Wahrscheinlichkeit ((N - r + 1) / N)^k - ((N - r) / N)^k gewählt.
  * `weights`: diese Wahrscheinlichkeiten je Rang.
  * `expected_curve`: E[T] und E[P] je k.
  * `curve_stats`: Minimum der Kurve, Anstieg danach (k = unendlich gegen das Minimum), Gewinn von k = 1 bis zum Minimum.
Quelle: Aufzählung aus Stück 5 und 6 der Linie (gleichstand-demo, hart-gegen-weich-demo); neu sind die Ordnungsstatistik, die drei Modelle und die Kennzahlen der Kurve.
"""

import numpy as np
from scipy.stats import spearmanr

import gdh_constants as C


def ks_for_exps(exps) -> list:
    """Die Gewichte k = 2^e; der Exponent K_INF steht für k = unendlich (None)."""
    return [None if e >= C.K_INF else 2 ** e for e in exps]


KS_ALL = ks_for_exps(range(C.K_EXP_MIN, C.K_EXP_MAX + 1))


def order_by(p: np.ndarray) -> np.ndarray:
    """Pläne nach P aufsteigend; bei Gleichstand die Reihenfolge der Aufzählung (stabil)."""
    return np.argsort(p, kind="stable")


def weights(n_plans: int, k: int | None) -> np.ndarray:
    """Wahrscheinlichkeit je Rang 1..N, dass Best-of-k den Plan auf diesem Rang wählt; k = None: der Plan auf Rang 1."""
    w = np.zeros(n_plans)
    if k is None:
        w[0] = 1.0
        return w
    r = np.arange(1, n_plans + 1, dtype=float)
    return ((n_plans - r + 1) / n_plans) ** k - ((n_plans - r) / n_plans) ** k


def expected_curve(p: np.ndarray, t: np.ndarray, ks=KS_ALL) -> tuple[np.ndarray, np.ndarray]:
    """E[T] und E[P] der Best-of-k-Wahl nach P für jedes k in ks (exakt)."""
    order = order_by(p)
    ts, ps = t[order], p[order]
    n_plans = len(p)
    et, ep = [], []
    for k in ks:
        w = weights(n_plans, k)
        et.append(float(w @ ts))
        ep.append(float(w @ ps))
    return np.array(et), np.array(ep)


def curve_stats(et: np.ndarray, ks=KS_ALL) -> dict:
    """Minimum der Kurve E[T](k): Ort, Anstieg danach (E[T] bei k = unendlich gegen das Minimum), Gewinn von k = 1 bis zum Minimum; ob das Optimum schlechter ist als ein Zufallsplan."""
    i = int(np.argmin(et))
    if et[-1] - et[i] <= 1e-9 * abs(et[i]):
        i = len(et) - 1                   # kein Anstieg: bei gleichem Wert zählt die größte Stärke (das Optimum), nicht ein Gitterpunkt davor
    rise = (et[-1] - et[i]) / et[i] if et[i] else 0.0
    return {"index": i, "k": ks[i], "e": C.K_INF if ks[i] is None else int(np.log2(ks[i])), "min": float(et[i]), "rise": float(rise), "declines": bool(rise > 1e-9),
            "gain": float((et[0] - et[i]) / et[0]) if et[0] else 0.0, "harm": bool(et[-1] > et[0])}


def percentile_of_optimum(p: np.ndarray, t: np.ndarray) -> float:
    """Anteil der Pläne, die bei T höchstens so gut sind wie das P-Optimum (0 = bester Plan, 1 = schlechtester)."""
    return float(np.mean(t <= t[int(np.argmin(p))]))


def rank_correlation(p: np.ndarray, t: np.ndarray) -> float:
    """Spearman-Rangkorrelation von P und T über alle Pläne."""
    return float(spearmanr(p, t).statistic)
