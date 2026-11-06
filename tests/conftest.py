"""Gemeinsame Fixtures: das Handbeispiel (n = 3), an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gdh_evaluation as ev  # noqa: E402
import gdh_scenario as S  # noqa: E402

HAND_A = np.array([[4, 4, 2], [2, 4, 6], [6, 3, 2]])
HAND_H = np.array([[2, 1, 3], [4, 4, 3], [5, 6, 1]])


@pytest.fixture
def hand_p() -> np.ndarray:
    """Ersatzziel P = Summe A je Plan (Reihenfolge von itertools.permutations).
    Pläne nach P aufsteigend mit (P, T), T = Summe A + Summe H: (2,0,1): (7, 20); (1,0,2): (8, 14); (0,1,2): (10, 17); (2,1,0): (12, 24); (0,2,1): (13, 24); (1,2,0): (16, 25).
    E[T] bei k = 1: 62/3; k = 2: 341/18; k = 4: 11753/648 (das Minimum der Kurve); k = unendlich: 20."""
    return S.plan_sums(HAND_A, 3)


@pytest.fixture
def hand_t(hand_p) -> np.ndarray:
    return hand_p + S.plan_sums(HAND_H, 3)


@pytest.fixture
def hand_analysis(hand_p, hand_t) -> ev.Analysis:
    import gdh_algorithm as A
    et, ep = A.expected_curve(hand_p, hand_t)
    return ev.Analysis(ev.Settings(3, 1, 0, 50, 0, 1, 21), hand_p.astype(float), hand_t.astype(float), {"A": HAND_A, "H": HAND_H}, et, ep)
