"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 3, 8, 8             # alle n! Pläne werden aufgezählt (bis 40 320)
SEED_MAX, DEFAULT_SEED = 999999, 100000

MODELS = ("noise", "hidden", "max")
MODEL_NAMES = {"noise": "Rauschen: P = T + Messfehler", "hidden": "Verdeckte Kosten: T = A + w · H", "max": "Falsches Maß: P = Summe, T = Maximum"}
MODEL_SHORT = {"noise": "Rauschen", "hidden": "Verdeckte Kosten", "max": "Summe statt Maximum"}
DEFAULT_MODEL = 0

SIGMA_MIN, SIGMA_MAX, SIGMA_STEP, DEFAULT_SIGMA = 0, 100, 5, 50      # Messfehler je Eintrag (Einträge 0 bis 100)
CORR_MIN, CORR_MAX, CORR_STEP, DEFAULT_CORR = -90, 90, 10, 0         # Korrelation r der verdeckten Kosten H mit A, in Prozent
W_MIN, W_MAX, DEFAULT_W = 1, 4, 1                                    # Gewicht der verdeckten Kosten im wahren Ziel
K_EXP_MIN, K_EXP_MAX, DEFAULT_K_EXP = 0, 21, 13                      # Optimierungsstärke k = 2^e; e = 21 steht für k = unendlich (das Optimum des Ersatzziels)
K_INF = K_EXP_MAX

SWEEP_SEEDS = tuple(range(100000, 100020))    # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
SWEEP_N = 8
SWEEP_SIGMAS = (5, 10, 25, 50, 100)
SWEEP_CORRS = (50, 0, -50, -90)               # in Prozent
SWEEP_WS = (1, 2)
SPEARMAN_SEEDS = SWEEP_SEEDS[:10]             # Rangkorrelation: die ersten zehn Instanzen
FRESH_DRAWS = 200                             # unabhängige zweite Messungen für den Vergleich mit frischen Daten

COLOR_ALL = "rgba(150,150,150,0.35)"
COLOR_T = "#c0504d"
COLOR_P = "#4c78a8"
COLOR_OK = "#2F6B65"
COLOR_MARK = "#d8a13a"

PRESETS = {
    "Rauschen: erst besser, dann schlechter": {"n": 8, "model": 0, "seed": 100000, "sigma": 50, "corr": 0, "w": 1, "k_exp": 13},
    "Der Fluch des Gewinners": {"n": 8, "model": 0, "seed": 100010, "sigma": 50, "corr": 0, "w": 1, "k_exp": 21},
    "Positive Korrelation schützt nicht": {"n": 8, "model": 1, "seed": 100004, "sigma": 50, "corr": 50, "w": 1, "k_exp": 21},
    "Das Optimum ist schlechter als ein Zufallsplan": {"n": 8, "model": 0, "seed": 100016, "sigma": 100, "corr": 0, "w": 1, "k_exp": 21},
    "Verdeckte Kosten: Optimieren bringt fast nichts": {"n": 8, "model": 1, "seed": 100014, "sigma": 50, "corr": -50, "w": 2, "k_exp": 21},
    "Verdeckte Kosten: Optimieren schadet sofort": {"n": 8, "model": 1, "seed": 100000, "sigma": 50, "corr": -90, "w": 2, "k_exp": 21},
    "Summe statt Maximum: meist harmlos": {"n": 8, "model": 2, "seed": 100000, "sigma": 50, "corr": 0, "w": 1, "k_exp": 21},
    "Kleinstes Beispiel (n = 3)": {"n": 3, "model": 1, "seed": 37, "sigma": 50, "corr": 0, "w": 1, "k_exp": 21},
}
PRESET_HELP = {
    "Rauschen: erst besser, dann schlechter": "Der wahre Wert ist bei k = 2^13 am besten (250,0; 39,3 % besser als bei k = 1) und steigt bis zum Optimum des Ersatzziels um 10,3 % auf 275,8.",
    "Der Fluch des Gewinners": "Am Optimum verspricht das Ersatzziel −49,9 (ein Messfehler macht Kosten negativ), und es gilt 291,5: die Wirklichkeit liegt 117 % über dem Versprechen.",
    "Positive Korrelation schützt nicht": "Spearman-Rangkorrelation 0,85 von Ersatzziel und wahrem Ziel, und trotzdem steigt der wahre Wert nach k = 2^11 um 17,2 %.",
    "Das Optimum ist schlechter als ein Zufallsplan": "Bei σ = 100 ist das Optimum des Ersatzziels (E[T] = 422,6) schlechter als ein Zufallsplan (400,3) und bei T schlechter als 61 % der Pläne.",
    "Verdeckte Kosten: Optimieren bringt fast nichts": "Das Optimieren bringt höchstens 1,2 % (bei k = 8) und schadet danach um 19,7 %; das Optimum ist bei T schlechter als 94 % der Pläne.",
    "Verdeckte Kosten: Optimieren schadet sofort": "Das Minimum liegt bei k = 1: jedes Optimieren des Ersatzziels verschlechtert den wahren Wert (Rangkorrelation −0,59), das Optimum ist schlechter als 96 % der Pläne.",
    "Summe statt Maximum: meist harmlos": "Die Summe als Ersatz für das Maximum: der wahre Wert wird mit jeder Stärke besser (52,5 % bis zum Optimum).",
    "Kleinstes Beispiel (n = 3)": "Sechs Pläne: E[T] ist bei k = 4 am besten (264,3), am Optimum des Ersatzziels 296,3 (12,1 % mehr).",
}
