"""Die Goodhart-Kurve - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 8 der Reihe „Zielfunktionsdesign“: dieselbe Zuordnung wie in Stück 1 bis 6, aber der Optimierer sieht nur ein Ersatzziel P, während das wahre Ziel T zählt.
Die Demo zeigt, wie sich T verhält, wenn man P stärker optimiert (Best-of-k, exakt gerechnet, bis zum Optimum), wo es am besten ist, wie stark es danach wieder steigt,
wie groß die Lücke zwischen Versprechen und Wirklichkeit ist und warum eine positive Korrelation nicht schützt.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import gdh_constants as C
from gdh_evaluation import (
    Settings,
    analyse,
    comparable,
    current,
    curve_rows,
    de,
    fresh_check,
    hidden_sweep,
    k_text,
    max_sweep,
    model_compare,
    noise_sweep,
    pct,
    spearman_sweep,
    summary,
    verdict_curve,
    verdict_current,
    verdict_fresh,
    verdict_gap,
    verdict_hidden_sweep,
    verdict_max_sweep,
    verdict_models,
    verdict_noise_sweep,
    verdict_spearman_sweep,
)
from gdh_layout import dunkles_design, kopf_css
from gdh_pdf_export import build_pdf
from gdh_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from gdh_visualization import build_cloud, build_curve, build_decline_bars

st.set_page_config(page_title="Die Goodhart-Kurve – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner="20 feste Instanzen werden gerechnet ...")
def _noise_sweep():
    return noise_sweep()


@st.cache_data(show_spinner="20 feste Instanzen werden gerechnet ...")
def _hidden_sweep():
    return hidden_sweep(), max_sweep()


@st.cache_data(show_spinner="Die Rangkorrelation wird auf 10 festen Instanzen gerechnet ...")
def _spearman_sweep():
    return spearman_sweep()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in gdh_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📈 Die Goodhart-Kurve")
st.markdown(
    """
**Was passiert, wenn man ein Ersatzziel stärker optimiert?** Dieselbe Aufgabe wie in Stück 1 bis 6: **n Personen** übernehmen **n Aufgaben**. Der Optimierer sieht aber nur ein **Ersatzziel P** (was gemessen wird);
was zählt, ist das **wahre Ziel T**. Beide sind Kosten, kleiner ist besser. Die **Optimierungsstärke k** heißt: unter k zufällig gezogenen Plänen den mit dem kleinsten P wählen; k = ∞ ist das Optimum von P.
Der Erwartungswert von T wird **exakt** gerechnet. Die Kurve zeigt, ob der wahre Wert mit der Stärke nur besser wird oder irgendwann wieder steigt.

Weiter unten: **🔬 Die Kurve**, **🔬 Der Fluch des Gewinners**, **🔬 Welche Art von Ersatzziel**, **🔬 Wie oft und wie viel?**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Vergleich", expanded=True):
    st.markdown(
        """
1. **Drei Rechenmodelle** (in Anlehnung an Arten von Ersatzzielen, nicht als Nachbau einer Arbeit): **Rauschen** (P ist T plus ein Messfehler je Eintrag), **verdeckte Kosten** (T enthält eine Kostenmatrix H, die P nicht sieht und die mit A korreliert) und **Summe statt Maximum** (P ist die Summe, T das Maximum).
2. **Optimierungsstärke:** k = 1 ist ein Zufallsplan, k = ∞ das Optimum des Ersatzziels. Die Erwartung von T und von P über die Wahl wird aus der Ordnungsstatistik gerechnet, ohne Zufall.
3. **Lücke:** der Fluch des Gewinners ist der Abstand zwischen dem Versprechen (P) und der Wirklichkeit (T) bei dem Plan, den der Optimierer wählt.
4. **Messungen, kein Satz:** Alle Zahlen sind Zählungen und Spannen über feste Instanzen dieser Rechenmodelle; sie sagen nichts über echte Kennzahlen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Personen und Aufgaben n", *bounds("n_slider"), key="n_slider", help="Alle n! Pläne werden aufgezählt (n = 8: 40 320).")
    model = st.selectbox("Ersatzziel", list(range(len(C.MODELS))), key="model_select", format_func=lambda i: C.MODEL_NAMES[C.MODELS[i]],
                         help="Rauschen und verdeckte Kosten brauchen die Regler darunter; „Summe statt Maximum“ keinen.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Parameter des Ersatzziels**")
    sigma = st.slider("Messfehler σ je Eintrag (nur Rauschen)", *bounds("sigma_slider"), key="sigma_slider", step=C.SIGMA_STEP,
                      help="Die Einträge liegen zwischen 0 und 100; der Messfehler ist normal verteilt, mittelwertfrei, unabhängig je Eintrag.")
    corr = st.slider("Korrelation r der verdeckten Kosten mit A in % (nur verdeckte Kosten)", *bounds("corr_slider"), key="corr_slider", step=C.CORR_STEP,
                     help="Negativ heißt: Wo A klein ist, ist die verdeckte Kostenmatrix H tendenziell groß.")
    w = st.slider("Gewicht w der verdeckten Kosten im wahren Ziel (nur verdeckte Kosten)", *bounds("w_slider"), key="w_slider", help="T = Summe A + w · Summe H.")
    st.markdown("**Optimierungsstärke**")
    k_exp = st.slider("Stärke k = 2^e (e = 21: k = ∞, das Optimum)", *bounds("k_exp_slider"), key="k_exp_slider",
                      help="k = 1 ist ein Zufallsplan; bei jedem Schritt wird unter doppelt so vielen gezogenen Plänen der mit dem kleinsten Ersatzziel gewählt; e = 21 steht für das Optimum des Ersatzziels.")

sync_query_params({"n_slider": int(n), "model_select": int(model), "seed_input": int(seed), "sigma_slider": int(sigma), "corr_slider": int(corr), "w_slider": int(w), "k_exp_slider": int(k_exp)})

settings = Settings(int(n), int(model), int(seed), int(sigma), int(corr), int(w), int(k_exp))
a = _analysis(settings)
stt = summary(a)
cur = current(a)
rows = curve_rows(a)
promise = comparable(settings.name)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: wie verhält sich der wahre Wert, wenn man das Ersatzziel stärker optimiert?")
m1, m2, m3 = st.columns(3)
m1.metric(f"Wahrer Wert E[T] bei k = {k_text(cur['e'])}", de(cur["et"]), delta=f"{pct(abs(cur['vs_1']))} {'besser' if cur['vs_1'] <= 0 else 'schlechter'} als k = 1", delta_color="off")
m2.metric("Bester wahrer Wert der Kurve", de(stt["min"]), delta=f"bei k = {k_text(stt['e'])}", delta_color="off")
m3.metric("Beim Optimum (k = ∞)", de(stt["et_inf"]), delta=f"{pct(stt['rise'])} über dem Minimum" if stt["declines"] else "kein Anstieg", delta_color="off")
st.plotly_chart(build_curve(rows, cur["e"], stt["e"], promise), width="stretch", key="curve_chart")
if promise:
    st.caption("Rot: der wahre Wert E[T], den man bekommt; blau gestrichelt: was das Ersatzziel verspricht, E[P]. Der Stern ist das Minimum von E[T], die Raute die eingestellte Stärke. Bei k = ∞ wählt der Optimierer genau einen Plan.")
else:
    st.caption("Rot: der wahre Wert E[T], den man bekommt. Der Stern ist das Minimum, die Raute die eingestellte Stärke. Beim Maß „Summe statt Maximum“ haben Ersatzziel und wahres Ziel verschiedene Einheiten; ein Versprechen gibt es nicht.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(a), file_name="goodhart-kurve.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist mehr Optimierung des Ersatzziels immer besser für das, was zählt?")
kind, text = verdict_curve(stt)
getattr(st, kind)(text)
kind, text = verdict_current(cur, stt)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Die Kurve")
st.caption("Alle Pläne mit Ersatzziel (waagerecht) und wahrem Ziel (senkrecht). Der Optimierer wählt den Plan ganz links; der wahre beste Plan liegt woanders.")
st.plotly_chart(build_cloud(a.p, a.t, stt["idx_p"], stt["idx_t"], cur["et"]), width="stretch", key="cloud_chart")
st.markdown(f"Der Optimierer wählt bei k = ∞ den Plan mit **P = {de(stt['p_opt'])}** und **T = {de(stt['t_of_p_opt'])}**; der wahre beste Plan hat **T = {de(stt['t_best'])}**. "
            f"Das P-Optimum ist bei T besser als {pct(1 - stt['percentile'])} der {stt['n_plans']} Pläne. Rangkorrelation von P und T über alle Pläne (Spearman): **{de(stt['spearman'], 2)}**.")

st.markdown("---")

st.subheader("🔬 Der Fluch des Gewinners")
st.caption("Je stärker der Optimierer auswählt, desto mehr wählt er Pläne, deren Ersatzziel zufällig oder systematisch zu gut aussieht: das Versprechen und die Wirklichkeit gehen auseinander.")
kind, text = verdict_gap(stt)
getattr(st, kind)(text)
if promise:
    rows_md = ["| Stärke k | Versprechen E[P] | Wirklichkeit E[T] | Lücke (T − P) / T |", "|---|---|---|---|"]
    for r in rows:
        if r["e"] in (0, 4, 8, 12, 16, 20, C.K_INF):
            rows_md.append(f"| {k_text(r['e'])} | {de(r['ep'])} | {de(r['et'])} | {pct(r['gap'], 0)} |")
    st.markdown("\n".join(rows_md))
fr = fresh_check(a)
if fr is not None:
    kind, text = verdict_fresh(fr)
    getattr(st, kind)(text)
else:
    st.caption("Eine frische Messung gibt es nur beim Rauschen (ein unabhängiger zweiter Messfehler); bei verdeckten Kosten fehlt dem Optimierer ein Teil der Wirklichkeit, den auch eine zweite Messung von A nicht liefert.")

st.markdown("---")

st.subheader("🔬 Welche Art von Ersatzziel")
st.caption("Dieselbe Größe und derselbe Seed mit den drei Rechenmodellen (mit den eingestellten Parametern).")
cmp_rows = model_compare(a)
rows_md = ["| Ersatzziel | Minimum bei k | Anstieg danach | Gewinn bis zum Minimum | Optimum bei T besser als | Spearman |", "|---|---|---|---|---|---|"]
for r in cmp_rows:
    rows_md.append(f"| **{C.MODEL_SHORT[r['model']]}** | {k_text(r['e'])} | " + (pct(r["rise"]) if r["declines"] else "–") + f" | {pct(r['gain'])} | {pct(1 - r['percentile'])} der Pläne | {de(r['spearman'], 2)} |")
st.markdown("\n".join(rows_md))
kind, text = verdict_models(cmp_rows)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Wie oft und wie viel?")
st.caption(f"Je {len(C.SWEEP_SEEDS)} feste Instanzen (SWEEP_SEEDS), n = {C.SWEEP_N}, alle aufgezählt; die Zahlen sind Zählungen und Spannen über Instanzen, kein Satz.")
if st.toggle("Rauschen über feste Instanzen nachrechnen (je σ)", value=False, key="sweep_noise"):
    noise_res = _noise_sweep()
    kind, text = verdict_noise_sweep(noise_res)
    getattr(st, kind)(text)
    st.plotly_chart(build_decline_bars([f"σ = {sg}" for sg in noise_res], [r["declines"] for r in noise_res.values()], [r["harm"] for r in noise_res.values()]), width="stretch", key="sweep_noise_chart")
if st.toggle("Verdeckte Kosten und Summe gegen Maximum nachrechnen (je w und r)", value=False, key="sweep_hidden"):
    hid_res, max_res = _hidden_sweep()
    kind, text = verdict_hidden_sweep(hid_res)
    getattr(st, kind)(text)
    st.plotly_chart(build_decline_bars([f"w = {w_}, r = {de(r_ / 100, 1)}" for (w_, r_) in hid_res], [x["declines"] for x in hid_res.values()], [x["harm"] for x in hid_res.values()]), width="stretch", key="sweep_hidden_chart")
    kind, text = verdict_max_sweep(max_res)
    getattr(st, kind)(text)
if st.toggle("Schützt eine positive Korrelation? Rangkorrelation und Anstieg nachrechnen", value=False, key="sweep_corr"):
    kind, text = verdict_spearman_sweep(_spearman_sweep(), _hidden_sweep()[0], _noise_sweep())
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Best-of-k als Optimierungsstärke** | Ein Gradientenverfahren, eine Population oder ein Löser mit Toleranz verstärken ihre Wirkung anders; die Kurve gilt für diese eine Art zu optimieren | Dokumentation des Verfahrens |
| **Drei Rechenmodelle, normaler Messfehler, Gauß-Kopula** | Schiefe Fehler, abhängige Fehler und andere Abhängigkeiten ändern die Kurve; die Namen der Arten von Ersatzzielen sind hier nur Anlehnung | Manheim und Garrabrant (nur Abstract gelesen) |
| **Der Anstieg ist eine Aussage über die Instanz** | Das P-Optimum ist ein einzelner Plan mit zufällig verzerrtem P; über andere Messfehler gemittelt sieht die Kurve anders aus | – |
| **n ≤ 8, alle Pläne aufgezählt** | Bei großen Planmengen kann man die Kurve nur noch schätzen | – |
| **Erwartung statt Einzelfall** | E[T] mittelt über die Ziehungen von k Plänen; ein einzelner Lauf kann besser oder schlechter sein | – |
| **Kein Vorschlag, wann man aufhört** | Das Minimum hängt an T, und T fehlt; die Demo zeigt, dass es von Instanz zu Instanz verschieden liegt | Stück 13 (Ziel testen) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Optimierungsstärke.** Gegeben $N$ Pläne mit Ersatzziel $P_j$ und wahrem Ziel $T_j$. Sortiert man nach $P$ aufsteigend (stabil), Rang $r = 1, \dots, N$. Zieht man $k$ Pläne gleichverteilt mit Zurücklegen und wählt den mit dem kleinsten $P$, wird der Plan auf Rang $r$ mit Wahrscheinlichkeit
$$q_r(k) = \left(\tfrac{N - r + 1}{N}\right)^{k} - \left(\tfrac{N - r}{N}\right)^{k}$$
gewählt. Die Summe der $q_r(k)$ ist 1; für $k = 1$ sind alle gleich $1/N$, für $k \to \infty$ gilt $q_1 \to 1$.

**Erwartung.** $\mathbb{E}[T](k) = \sum_r q_r(k)\, T_{(r)}$ und $\mathbb{E}[P](k) = \sum_r q_r(k)\, P_{(r)}$; $k = \infty$ ist der Plan auf Rang 1. $\mathbb{E}[P](k)$ ist nicht steigend in $k$; $\mathbb{E}[T](k)$ kann steigen. **Anstieg** heißt $(\mathbb{E}[T](\infty) - \min_k \mathbb{E}[T](k)) / \min_k \mathbb{E}[T](k)$.

**Modelle.** *Rauschen:* $T = \sum a_{i\pi(i)}$, $P = \sum (a_{i\pi(i)} + \varepsilon_{i\pi(i)})$ mit $\varepsilon \sim \mathcal{N}(0, \sigma^2)$ unabhängig. *Verdeckt:* $P = \sum a_{i\pi(i)}$, $T = P + w \sum h_{i\pi(i)}$; $a = 100\,\Phi(z_1)$, $h = 100\,\Phi(r z_1 + \sqrt{1 - r^2} z_2)$ mit unabhängigen Standardnormalen $z_1, z_2$ (Gauß-Kopula, Korrelation $r$ der Normalen). *Falsches Maß:* $P = \sum a_{i\pi(i)}$, $T = \max_i a_{i\pi(i)}$.

**Lücke.** $(\mathbb{E}[T] - \mathbb{E}[P]) / \mathbb{E}[T]$ (nur wenn $P$ und $T$ dieselbe Einheit haben). **Frische Messung.** Ist $\varepsilon'$ eine unabhängige zweite Messung, so gilt für jeden festen Plan $\mathbb{E}[P'] = T$: die Lücke verschwindet im Mittel auf frischen Daten, nicht auf den Daten, die ausgewählt haben.

**Literatur.** Manheim und Garrabrant, „Categorizing Variants of Goodhart's Law“ (arXiv 1803.04585): Überoptimierung auf Basis von Metriken, wenn eine Metrik „to an extent that further optimization is ineffective or harmful“ benutzt wird (Abstract gelesen; die Namen der vier Arten stehen dort nicht). Gao, Schulman und Hilton, „Scaling Laws for Reward Model Overoptimization“ (arXiv 2210.10760): Proxy-Belohnung zu stark zu optimieren kann die „ground truth performance“ verschlechtern, gemessen unter anderem mit Best-of-n-Sampling (Abstract gelesen; die Funktionsformen stehen dort nicht). Smith und Winkler, „The Optimizer's Curse“ (Management Science 2006): nicht gelesen. Diese Demo übernimmt keine Zahl daraus; alle Zahlen sind Messungen an den Rechenmodellen der Demo.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
