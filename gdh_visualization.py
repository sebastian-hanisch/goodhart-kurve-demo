"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import gdh_constants as C
from gdh_evaluation import k_text


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_curve(rows: list[dict], cur_e: int, min_e: int, show_promise: bool = True):
    """Die Goodhart-Kurve: E[T] (wahrer Wert, rot) und E[P] (das Versprechen, blau gestrichelt) je Optimierungsstärke k; Stern: Minimum; Raute: die eingestellte Stärke."""
    xs = [k_text(r["e"]) for r in rows]
    fig = go.Figure(go.Scatter(x=xs, y=[r["et"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_T), marker=dict(size=5), name="wahrer Wert E[T]",
                               hovertemplate="k = %{x}: E[T] %{y:.1f}<extra></extra>"))
    if show_promise:
        fig.add_trace(go.Scatter(x=xs, y=[r["ep"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_P, dash="dash"), marker=dict(size=5), name="Versprechen E[P]",
                                 hovertemplate="k = %{x}: E[P] %{y:.1f}<extra></extra>"))
    lo = {r["e"]: r for r in rows}
    fig.add_trace(go.Scatter(x=[k_text(min_e)], y=[lo[min_e]["et"]], mode="markers", marker=dict(symbol="star", size=16, color=C.COLOR_OK, line=dict(width=1.5, color="white")), name="bester wahrer Wert",
                             hovertemplate="Minimum bei k = %{x}: %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[k_text(cur_e)], y=[lo[cur_e]["et"]], mode="markers", marker=dict(symbol="diamond", size=13, color=C.COLOR_MARK, line=dict(width=1.5, color="white")), name="eingestellte Stärke",
                             hovertemplate="k = %{x}: %{y:.1f}<extra></extra>"))
    fig.update_xaxes(type="category", title_text="Optimierungsstärke k (unter k gezogenen Plänen den mit dem kleinsten Ersatzziel wählen; ∞: das Optimum)")
    fig.update_yaxes(title_text="Erwartung (Kosten, kleiner ist besser)")
    return _base(fig, height=400)


def build_cloud(p: np.ndarray, t: np.ndarray, idx_p: int, idx_t: int, et_now: float):
    """Alle Pläne (Ersatzziel gegen wahres Ziel); das P-Optimum und der wahre beste Plan sind markiert, die waagerechte Linie ist E[T] bei der eingestellten Stärke."""
    fig = go.Figure(go.Scattergl(x=p, y=t, mode="markers", marker=dict(size=3, color=C.COLOR_ALL), name="alle Pläne", hovertemplate="P %{x:.1f} / T %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[p[idx_p]], y=[t[idx_p]], mode="markers", marker=dict(symbol="diamond", size=14, color=C.COLOR_MARK, line=dict(width=1.5, color="white")), name="P-Optimum (was der Optimierer wählt)",
                             hovertemplate="P-Optimum: P %{x:.1f} / T %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[p[idx_t]], y=[t[idx_t]], mode="markers", marker=dict(symbol="star", size=16, color=C.COLOR_OK, line=dict(width=1.5, color="white")), name="wahrer bester Plan",
                             hovertemplate="bester Plan: P %{x:.1f} / T %{y:.1f}<extra></extra>"))
    fig.add_hline(y=et_now, line=dict(color=C.COLOR_T, dash="dash"), annotation_text="E[T] bei der eingestellten Stärke", annotation_position="top left")
    fig.update_xaxes(title_text="Ersatzziel P (das wird gemessen und optimiert)")
    fig.update_yaxes(title_text="Wahres Ziel T (das zählt)")
    return _base(fig, height=400)


def build_decline_bars(labels: list[str], counts: list[int], harm: list[int], total: int = 20):
    """Instanzen mit Anstieg nach dem Minimum und Instanzen, in denen das Optimum schlechter ist als ein Zufallsplan, je Einstellung."""
    fig = go.Figure([go.Bar(x=labels, y=counts, name="Anstieg nach dem Minimum", marker_color=C.COLOR_MARK, hovertemplate="%{x}: %{y} von " + str(total) + "<extra></extra>"),
                     go.Bar(x=labels, y=harm, name="Optimum schlechter als ein Zufallsplan", marker_color=C.COLOR_T, hovertemplate="%{x}: %{y} von " + str(total) + "<extra></extra>")])
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(range=[0, total], title_text=f"Instanzen (von {total})")
    return _base(fig, height=340)
