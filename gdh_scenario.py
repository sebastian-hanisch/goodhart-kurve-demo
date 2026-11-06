"""Szenario: n Personen, n Aufgaben; ein Ersatzziel P (was gemessen und optimiert wird) und ein wahres Ziel T (was zählt), beide Summen über einen Plan, kleiner ist besser. Alles simuliert.

Drei Rechenmodelle (in Anlehnung an die Arten von Ersatzzielen, die Manheim und Garrabrant unterscheiden; hier nur Rechenmodelle):
  noise   P = Summe (A + Messfehler),  T = Summe A;  Einträge von A gleichverteilt 0 bis 100, Messfehler normal mit Standardabweichung sigma, unabhängig je Eintrag
  hidden  P = Summe A,  T = Summe A + w * Summe H;  H eine verdeckte Kostenmatrix, mit A über eine Gauß-Kopula mit Korrelation r verbunden (Einträge 0 bis 100)
  max     P = Summe A,  T = Maximum A (das, was Stück 1 und 2 „fair“ nannten)
Die Erzeugung entspricht den Messreihen der Planung (gleiche Seeds, gleiche Reihenfolge der Ziehungen)."""

import itertools
from functools import lru_cache

import numpy as np
from scipy.special import ndtr


@lru_cache(maxsize=None)
def all_plans(n: int) -> np.ndarray:
    """Alle n! Pläne als Zeilen (Reihenfolge von itertools.permutations); nur bis n = 9."""
    if not 1 <= n <= 9:
        raise ValueError(f"n = {n}: Aufzählung nur für 1 bis 9 Personen")
    return np.array(list(itertools.permutations(range(n))), dtype=np.int16)


def plan_sums(m: np.ndarray, n: int) -> np.ndarray:
    return m[np.arange(n)[None, :], all_plans(n)].sum(axis=1)


def plan_maxes(m: np.ndarray, n: int) -> np.ndarray:
    return m[np.arange(n)[None, :], all_plans(n)].max(axis=1)


def make_noise(n: int, seed: int, sigma: float) -> tuple[np.ndarray, np.ndarray, dict]:
    """Rauschen: (P, T, Matrizen). Der Messfehler ist je Eintrag unabhängig und mittelwertfrei."""
    rng = np.random.default_rng(seed)
    a = rng.uniform(0.0, 100.0, (n, n))
    noise = rng.normal(0.0, sigma, (n, n))
    return plan_sums(a + noise, n), plan_sums(a, n), {"A": a, "noise": noise}


def make_hidden(n: int, seed: int, corr: float, w: float) -> tuple[np.ndarray, np.ndarray, dict]:
    """Verdeckte Kosten: (P, T, Matrizen). corr in [-1, 1]; Gauß-Kopula zwischen A und H."""
    rng = np.random.default_rng(seed)
    z1 = rng.standard_normal((n, n))
    z2 = rng.standard_normal((n, n))
    a = 100.0 * ndtr(z1)
    h = 100.0 * ndtr(corr * z1 + np.sqrt(1.0 - corr * corr) * z2)
    return plan_sums(a, n), plan_sums(a, n) + w * plan_sums(h, n), {"A": a, "H": h}


def make_max(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, dict]:
    """Falsches Maß: (P, T, Matrizen)."""
    rng = np.random.default_rng(seed)
    a = rng.uniform(0.0, 100.0, (n, n))
    return plan_sums(a, n), plan_maxes(a, n), {"A": a}


def make_model(model: str, n: int, seed: int, sigma: float = 50.0, corr: float = 0.0, w: float = 1.0) -> tuple[np.ndarray, np.ndarray, dict]:
    if model == "noise":
        return make_noise(n, seed, sigma)
    if model == "hidden":
        return make_hidden(n, seed, corr, w)
    if model == "max":
        return make_max(n, seed)
    raise ValueError(f"unbekanntes Modell: {model}")
