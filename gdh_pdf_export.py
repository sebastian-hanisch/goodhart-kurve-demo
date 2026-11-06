"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import gdh_constants as C
from gdh_evaluation import Analysis, current, de, k_text, summary

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "σ": "sigma", "∞": "unendlich", "„": '"', "“": '"', "²": "2"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis) -> bytes:
    s = a.settings
    st, cur = summary(a), current(a)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Die Goodhart-Kurve"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    extra = f", sigma {s.sigma}" if s.name == "noise" else (f", r {de(s.corr / 100, 1)}, w {s.w}" if s.name == "hidden" else "")
    pdf.multi_cell(0, 5, _s(f"{s.n} Personen, {s.n} Aufgaben, Modell: {C.MODEL_NAMES[s.name]}{extra}, Seed {s.seed}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.multi_cell(0, 5, _s(f"Bester wahrer Wert bei k = {k_text(st['e'])}: E[T] = {de(st['min'])} ({de(st['gain'] * 100)} % besser als bei k = 1); beim Optimum des Ersatzziels E[T] = {de(st['et_inf'])} "
                            f"({de(st['rise'] * 100)} % mehr als das Minimum). Das Optimum ist bei T besser als {de(100 - st['percentile'] * 100)} % der Pläne."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _s(f"Eingestellte Stärke k = {k_text(cur['e'])}: E[T] = {de(cur['et'])}" + (f", Versprechen E[P] = {de(cur['ep'])}." if cur["gap"] is not None else ".")), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Optimierungsstärke k: unter k zufällig gezogenen Plänen den mit dem kleinsten Ersatzziel wählen (Erwartung exakt). Quelle: goodhart-kurve-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
