# Die Goodhart-Kurve – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-goodhart-kurve-demo.streamlit.app/)** -->

Stück 8 der Linie **Zielfunktionsdesign** („Das Ziel ist das Modell“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt). Es baut auf Stück 1 bis 6 auf (`zielvergleich-demo`, `preis-der-fairness-demo`, `zwei-kriterien-demo`, `lexikographisch-demo`, `gleichstand-demo`, `hart-gegen-weich-demo`; Stück 7 ist zurückgestellt): dieselbe Zuordnung, jetzt mit **zwei Zielen, von denen der Optimierer nur eines sieht**. Das **Ersatzziel P** wird gemessen und optimiert, das **wahre Ziel T** zählt; beide sind Kosten, kleiner ist besser. Die **Optimierungsstärke k** heißt: unter k zufällig gezogenen Plänen den mit dem kleinsten P wählen (Best-of-k); k = ∞ ist das Optimum von P. Der Erwartungswert von T über diese Wahl wird **exakt** gerechnet. Alles ist **simuliert**; keine Aussage über echte Kennzahlen, Personen oder Betriebe.

## Warum dieses Problem

Wer eine Kennzahl optimiert, die nur ein Ersatz für das ist, was zählt, verbessert das Eigentliche zuerst und verschlechtert es bei den meisten Instanzen ab einem Punkt wieder; dieser Punkt ist von Instanz zu Instanz verschieden, und eine positive Korrelation von Ersatz und Wahrem schützt nicht. Die Fragen: Wo ist der wahre Wert am besten? Wie stark steigt er danach? Wie groß ist die Lücke zwischen Versprechen und Wirklichkeit (der Fluch des Gewinners)? Ist das Optimum des Ersatzziels sogar schlechter als ein Zufallsplan?

## Modell

Gegeben `N` Pläne (alle `n!` Zuordnungen von n Personen auf n Aufgaben, bis n = 8: 40 320) mit Ersatzziel `P_j` und wahrem Ziel `T_j`. Sortiert man nach P aufsteigend (stabil), wird bei Best-of-k der Plan auf Rang `r` mit Wahrscheinlichkeit `((N − r + 1)/N)^k − ((N − r)/N)^k` gewählt; daraus folgen `E[T](k)` und `E[P](k)` **exakt**, `k = ∞` ist der Plan auf Rang 1. **Anstieg** heißt `(E[T](∞) − min_k E[T](k)) / min_k E[T](k)`; **Gewinn** ist die Verbesserung von `k = 1` bis zum Minimum in Prozent von `E[T](1)`; die **Lücke** ist `(E[T] − E[P]) / E[T]`. Drei Rechenmodelle (in Anlehnung an Arten von Ersatzzielen, nicht als Nachbau einer Arbeit): **Rauschen** (`P = Σ(A + Messfehler)`, `T = Σ A`, Messfehler normal mit Standardabweichung `σ`, unabhängig je Eintrag, Einträge 0 bis 100), **verdeckte Kosten** (`P = Σ A`, `T = Σ A + w · Σ H` mit einer verdeckten Matrix `H`, die über eine Gauß-Kopula mit Korrelation `r` an `A` hängt) und **Summe statt Maximum** (`P = Σ A`, `T = max A`). Formeln stehen im 📐-Expander der App.

## Methodik

Alle `n!` Pläne werden aufgezählt (bis n = 8). Optimierungsstärke `k = 2⁰` bis `2²⁰` und `∞`; die Erwartung ist exakt, in der App gibt es keinen Zufall. Die App zeigt: die Kurve `E[T](k)` mit dem Versprechen `E[P](k)`, die Punktwolke aller Pläne mit dem P-Optimum und dem wahren besten Plan, die Lücke je Stärke, eine frische Messung des P-Optimums (nur Rauschen), die drei Modelle nebeneinander auf derselben Instanz und Zählungen über 20 feste Instanzen hinter Schaltern. Verdikte entstehen live aus der Rechnung, jede Zahl im Text kommt aus dem Ergebnis.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus den Auswertungsfunktionen der App und sind in `tests/test_claims.py` nachgerechnet. „Je 20 feste Instanzen“ heißt `SWEEP_SEEDS` (Seeds 100000 bis 100019), nie ein einzelner Seed; die Zahlen sind **Zählungen und Spannen über Instanzen**, kein Satz und keine Aussage über andere Instanzen. Soweit nicht anders angegeben n = 8 (alle 40 320 Pläne aufgezählt). Der **Anstieg** gilt je Instanz: das Optimum des Ersatzziels ist ein einzelner Plan mit verzerrtem P, kein Mittel über Verteilungen.

| Frage | Befund |
|---|---|
| Rauschen, σ = 5 / 10 / 25 / 50 / 100: Instanzen mit Anstieg nach dem Minimum | **7 / 13 / 12 / 16 / 12** von 20; Anstieg Median 0,0 % / 0,6 % / 0,5 % / 2,7 % / 3,4 %, Maximum 6,6 % / 9,0 % / 11,0 % / 23,4 % / 16,1 % |
| dabei: das Optimum des Ersatzziels ist **schlechter als ein Zufallsplan** in | **0 / 0 / 0 / 1 / 3** von 20 |
| Gewinn von k = 1 bis zum Minimum (Median) | 66,5 % / 60,7 % / 54,7 % / 39,3 % / 32,7 % |
| Fluch des Gewinners: Lücke `(T − P) / T` am Optimum des Ersatzziels (Median) | 8,2 % / 30,1 % / 84,4 % / 169,9 % / 303,3 % |
| Perzentil des P-Optimums bei T (0 = bester Plan; Median) | 0,0 % / 0,0 % / 0,1 % / 3,3 % / 5,6 % |
| Verdeckte Kosten, w = 1, r = +0,5 / 0,0 / −0,5 / −0,9: Instanzen mit Anstieg | **11 / 17 / 17 / 16** von 20; Anstieg Median 0,3 % / 2,1 % / 2,6 % / 1,4 %, Maximum 17,2 % / 20,9 % / 16,8 % / 7,8 %; Optimum schlechter als Zufallsplan in **0 / 0 / 1 / 5**; Gewinn Median 45,7 % / 31,8 % / 16,5 % / 3,5 % |
| Verdeckte Kosten, w = 2, dieselben r | Anstieg in **13 / 17 / 17 / 20** von 20; Median 0,9 % / 4,0 % / 6,8 % / **20,5 %**, Maximum 23,8 % / 29,0 % / 30,3 % / 29,3 %; Optimum schlechter als Zufallsplan in **0 / 4 / 11 / 20**; Gewinn Median 41,2 % / 20,7 % / 1,3 % / 0,0 %; Minimum der Kurve im Median bei k = 49 152 / 8 192 / 12 / 1 |
| Verdeckte Kosten, w = 2, r = −0,9 | Das Optimum ist bei T im Median **schlechter als 99,8 %** der Pläne (Perzentil des P-Optimums 99,8 %) |
| Summe als Ersatz für das Maximum | Anstieg in **8** von 20 (Median 0,0 %, Maximum 7,7 %), Optimum schlechter als Zufallsplan in **0**; Gewinn Median 58,7 %; Perzentil des P-Optimums bei T Median 0,0 %, Maximum 1,3 %: hier meist harmlos |
| Rangkorrelation (Spearman) von P und T über alle Pläne (Median über 10 Instanzen) | Rauschen σ = 25: **0,78**; verdeckt w = 1, r = +0,5: **0,84**; r = −0,5: **0,50**; w = 2, r = −0,9: **−0,62**; Summe gegen Maximum: **0,49** |
| Schützt die Korrelation? | Trotz 0,78 steigt T nach dem Minimum in **12** von 20 Instanzen (Rauschen σ = 25), trotz 0,84 in **11** von 20 (verdeckt, w = 1, r = +0,5) |
| Preset „Rauschen: erst besser, dann schlechter“ (n = 8, Seed 100000, σ = 50) | Minimum bei k = 2¹³ mit E[T] = **250,0** (**39,3 %** besser als bei k = 1), danach Anstieg um **10,3 %** auf **275,8**; am Optimum verspricht P = **−153,1**, es gilt T = 275,8 (Lücke **155,5 %**), der wahre beste Plan hat T = **148,8** |
| Preset „Der Fluch des Gewinners“ (Seed 100010) | am Optimum verspricht P = **−49,9**, es gilt T = **291,5**: Lücke **117,1 %**; Minimum bei k = 2¹⁵ mit 277,1, Anstieg **5,2 %** |
| Preset „Das Optimum ist schlechter als ein Zufallsplan“ (σ = 100, Seed 100016) | E[T] am Optimum **422,6**, bei einem Zufallsplan **400,3**; Minimum bei k = 2¹¹ mit **364,1**, Anstieg **16,1 %**; schlechter als **61,2 %** der Pläne |
| Preset „Positive Korrelation schützt nicht“ (w = 1, r = +0,5, Seed 100004) | Spearman **0,85**, Minimum bei k = 2¹¹ mit **476,1**, Anstieg **17,2 %** auf **557,9** |
| Preset „Verdeckte Kosten: Optimieren bringt fast nichts“ (w = 2, r = −0,5, Seed 100014) | Gewinn nur **1,2 %** (Minimum bei k = 8), danach Anstieg um **19,7 %**; das Optimum ist bei T besser als nur **5,8 %** der Pläne |
| Preset „Verdeckte Kosten: Optimieren schadet sofort“ (w = 2, r = −0,9, Seed 100000) | Minimum bei **k = 1** (E[T] = **1198,6**), das Optimum **1355,5** (**13,1 %** mehr), Spearman **−0,59** |
| Preset „Summe statt Maximum: meist harmlos“ (Seed 100000) | E[T] fällt von **92,6** (k = 1) auf **44,0** (k = ∞): **52,5 %** Gewinn, kein Anstieg |
| Preset „Kleinstes Beispiel“ (n = 3, verdeckt, w = 1, r = 0, Seed 37) | Minimum bei k = **4** mit **264,3** (**11,7 %** besser als k = 1), am Optimum **296,3** (**12,1 %** mehr), Lücke **69,6 %** |

**Korrektur der Planungshypothese:** Vor der Messung stand „wahrer Wert steigt zuerst und fällt dann“. Das trägt für Rauschen und verdeckte Kosten in der Mehrzahl der Instanzen, aber nicht in allen, und nicht als glatte Kurve: der Anstieg liegt im letzten Schritt vom „sehr scharfen Zufall“ zum **einen** Plan, der das Ersatzziel minimiert. Die erste Fassung der Messung (Gitter bis k = 2¹⁵ ohne den Endpunkt ∞) hatte den Anteil **zu klein** gemessen (6 statt 13 von 20 bei σ = 10), und der Zähler „schlechter als Zufallsplan“ stand in zwei Teilen auf 0, bis das Gegenlesen (Minimum bei k = 1, aber Zähler 0) es zeigte. Die Summe für das Maximum zu optimieren ist dagegen meistens harmlos. Von der Literatur ist nur gelesen: Manheim und Garrabrant (arXiv 1803.04585, Abstract): Überoptimierung, wenn eine Metrik „to an extent that further optimization is ineffective or harmful“ benutzt wird; die Namen der vier Arten stehen im Abstract nicht. Gao, Schulman und Hilton (arXiv 2210.10760, Abstract): ein Proxy zu stark zu optimieren kann „ground truth performance“ verschlechtern, gemessen unter anderem mit Best-of-n-Sampling; die Funktionsformen stehen im Abstract nicht. Smith und Winkler (Optimizer's Curse, Management Science 2006) sind nicht gelesen.

## Ehrliche Grenzen

- **Ein Verfahren der Optimierung:** Best-of-k ist eine Art, „stärker zu optimieren“; Gradientenverfahren, Populationen und Löser mit Toleranz verstärken ihre Wirkung anders.
- **Drei Rechenmodelle:** normaler, unabhängiger Messfehler und eine Gauß-Kopula; schiefe oder abhängige Fehler ändern die Kurve. Die Namen der Arten von Ersatzzielen sind nur Anlehnung.
- **Kein Satz über Verteilungen:** Der Anstieg ist eine Aussage über die einzelne Instanz (ein Plan mit zufällig verzerrtem P); über andere Messfehler gemittelt sieht die Kurve anders aus. Die Zahlen sind Zählungen über 20 feste Instanzen.
- **Negative Kosten im Versprechen:** Ein Messfehler kann die gemessenen Kosten eines Plans unter null drücken (das Versprechen P ist dann negativ); das ist Teil des Modells, nicht ein Fehler.
- **Kein Stopp-Vorschlag:** Das Minimum hängt an T, und T fehlt dem Optimierer; die Demo zeigt, dass es von Instanz zu Instanz verschieden liegt (k = 1 bis über 2 Millionen).
- **n ≤ 8:** Alle Pläne sind aufgezählt; bei großen Planmengen ließe sich die Kurve nur schätzen.

## Verifikation

Insgesamt 273 Tests (`pytest tests/`), alle grün.

- **Kern:** Handbeispiel (n = 3, sechs Pläne) von Hand: P und T aller Pläne, Gewichte für k = 1, 2, ∞, `E[T]` bei k = 1, 2, 4, ∞ als Brüche (62/3, 341/18, 11753/648, 20), das Minimum bei k = 4, Lücke 65 %, Perzentil, Rangkorrelation gegen eine reine Python-Rechnung; die Formel der Ordnungsstatistik gegen die **vollständige Aufzählung aller N^k Ziehungen** (mit `fractions.Fraction`, ganze Zahlen mit Gleichständen in P) und gegen eine unabhängige Monte-Carlo-Rechnung mit festem Seed; 2²⁰ gegen ∞; eine reine Python-Kurve für jedes Modell.
- **Eigenschaften:** die Gewichte sind Wahrscheinlichkeiten und summieren sich zu 1; `E[T](1)` ist der Mittelwert aller T; das Versprechen `E[P](k)` wird nie schlechter; bei P = T fällt die Kurve und endet im Optimum, bei gegenläufigem P steigt sie nur; die Erwartung hängt nicht von der Reihenfolge der Pläne ab und skaliert linear; mehr Rauschen, größere Lücke am Optimum; Determinismus.
- **Randfälle:** ein Plan, zwei Pläne von Hand, alle P gleich (Reihenfolge der Aufzählung), sehr großes k, die Grenzen der Kopula (r = ±1), jedes Modell bei n = 3, 4, 8 und an den Reglergrenzen, kein Versprechen beim Maß „Summe statt Maximum“.
- **Verdikte:** reine Funktionen, jede Verzweigung und jede Zahl im Text an Hand- oder Presetwerten (`tests/test_verdicts.py`).
- **Presets:** Vollständigkeit, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, kein anderes Preset gleich den Voreinstellungen, und dass jedes Preset zeigt, was sein Name sagt.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), jedes Preset, jedes Modell, jede Stärke, Parametergrenzen, alle Schalter, Footer-Test, Layout.
- **Claims:** jede Zahl dieser README in `tests/test_claims.py`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `gdh_algorithm.py` | Kern: Gewichte der Ordnungsstatistik, Erwartung, Kennzahlen der Kurve, Perzentil, Rangkorrelation |
| `gdh_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `gdh_evaluation.py` | Experimente, Sweeps, Verdikte |
| `gdh_layout.py` | Fester Kopf (Stylesheet) |
| `gdh_pdf_export.py` | PDF-Export des Ergebnisses |
| `gdh_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `gdh_scenario.py` | Aufzählung, die drei Rechenmodelle (Rauschen, verdeckte Kosten, Summe statt Maximum) |
| `gdh_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handbeispiel, Orakel, Eigenschaften, Randfälle, Verdikte, Presets, Claims, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Keine Ausnutzung des Ersatzziels:** Was ein Optimierer aus einer Lücke im Modell macht, ist Stück 9, was er verlagert, Stück 10; hier nur die Kurve.
- **Kein Stopp und keine Gegenmaßnahme:** Wie man das Ziel vor dem Einsatz testet, ist Stück 13.
- **Kein Gradientenverfahren, keine Population:** Best-of-k ist die einzige Optimierungsstärke.
- **Keine Nachbauten der Literatur:** Weder die Funktionsformen von Gao u. a. noch die vier Arten von Manheim und Garrabrant sind nachgebaut (nur die Abstracts sind gelesen).
- **Keine Schätzung bei großen Planmengen:** n ≤ 8, alle Pläne aufgezählt.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
