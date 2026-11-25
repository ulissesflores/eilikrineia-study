# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Draw the README pictures as code, in the five languages of the READMEs, light and dark.

The banners, the design diagram and the translated figures are drawn from the frozen score files
and outputs, so that every number in a picture is read from the package and none is typed by hand.

Claim map (no picture without a claim)
--------------------------------------
- ``banner-<lang>-{light,dark}.svg``: the title and the thesis. The two bars are study 2's
  measured shares for the arm with the record: work that passed the hidden check and agents that
  said "complete". They are read from ``runs/study2-analysis.txt``; the trial total is counted
  in the four per-trial score files.
- ``design-<lang>-{light,dark}.svg``: the four experiments, what each compared and how many
  trials each ran. Trial counts are read from the per-trial score files.
- ``assets/figures/<figure>-<lang>-{light,dark}.{png,svg}``: the three figures of the Results
  section, drawn by the sealed ``scripts/make_figures.py`` (imported unchanged; every number is
  read there from the frozen files under ``runs/``) with each piece of text translated just
  before saving. A string without a translation stops the script, so no English is left behind.
- ``lab-lockup-dark.png``: the Codex Hash Research Laboratory mark for dark backgrounds,
  derived from the original ``lab-lockup-light.png`` (black strokes become the dark ink).

The English README keeps ``banner-{light,dark}.svg``, ``design-{light,dark}.svg`` and the
figures under ``output/figures/``; the other four languages (``pt-BR``, ``es``, ``it``, ``he``)
get their own files. Numbers are written in each language's format. Hebrew pictures are drawn
mirrored, right to left; the axes of the three data figures keep their left-to-right numeric
direction and only their text is Hebrew. Bidirectional text needs matplotlib 3.11 or newer,
which ships libraqm. Text is converted to outlines and the SVG hash salt is fixed, so the
pictures look the same without any installed font and do not change between runs.

Inputs
------
- runs/study2-analysis.txt and the four per-trial score files in runs/ (pilot-scores.csv,
  study-scores.csv, study2-scores.csv, study3-scores.csv).
- scripts/make_figures.py (imported unchanged) and the frozen files under runs/ it reads.
- assets/brand/lab-lockup-light.png, from which the dark lockup is derived.

Outputs
-------
- Deterministic SVG and PNG files, written to assets/brand/ (banners, design diagrams, dark lockup)
  and assets/figures/ (translated figures). One summary line is printed.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python assets/brand/make_brand.py

Status
------
Presentation tooling for the READMEs; it is not an analysis, and no number is computed here that
is not already in the frozen outputs.

Author
------
Carlos Ulisses Flores, ORCID https://orcid.org/0000-0002-6034-7765

Repository
----------
https://github.com/ulissesflores/eilikrineia-study
"""

import csv
import importlib.util
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from matplotlib.text import Text  # noqa: E402

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
RUNS = ROOT / "runs"
FIGURES = ROOT / "assets" / "figures"
SCORES = ("pilot-scores", "study-scores", "study2-scores", "study3-scores")
THEMES = {
    "light": {
        "bg": "#F6F8FA",
        "ink": "#0B1B2B",
        "muted": "#5B6B7B",
        "line": "#D8DEE4",
        "amber": "#B86E00",
        "teal": "#0F766E",
        "card": "#FFFFFF",
    },
    "dark": {
        "bg": "#0D1117",
        "ink": "#E6EDF3",
        "muted": "#9BA7B4",
        "line": "#30363D",
        "amber": "#F5A524",
        "teal": "#2DD4BF",
        "card": "#161B22",
    },
}
plt.rcParams.update(
    {"font.family": "DejaVu Sans", "svg.fonttype": "path", "svg.hashsalt": "eilikrineia"}
)

# Text of every picture, per language. "dec" is the decimal separator (the thousands separator is
# the other one of "," and "."); "rtl" draws the banner and the diagram mirrored.
LANGS = {
    "en": {
        "dec": ".",
        "rtl": False,
        "title": ("Claim records", "and what a coding agent says"),
        "thesis": "It changed what the agent said. It did not change the work.",
        "sub": "Four experiments · {total} trials · hidden checks",
        "did": "did the work",
        "said": 'said "complete"',
        "bars": "study 2, agents with the record",
        "trials": "{n} trials",
        "cards": (
            (
                "PILOT",
                "Does a signed, public\nrecord change claims?",
                "No effect at this size. The\nmeasure was mostly artefact.",
            ),
            (
                "STUDY 1",
                "Published record against\na privately kept one",
                "No detectable effect\nof publicity.",
            ),
            (
                "STUDY 2",
                "Claim record with evidence\nagainst no record",
                'Says "complete" half as\noften. Same work.',
            ),
            (
                "STUDY 3",
                "Instruction, pressure and\nacceptance tests",
                "No arm showed a gain\non five tests.",
            ),
        ),
    },
    "pt-BR": {
        "dec": ",",
        "rtl": False,
        "title": ("Registros de afirmações", "e o que um agente de programação diz"),
        "thesis": "Mudou o que o agente disse. Não mudou o trabalho.",
        "sub": "Quatro experimentos · {total} tentativas · verificações ocultas",
        "did": "fez o trabalho",
        "said": 'disse "completo"',
        "bars": "estudo 2, agentes com o registro",
        "trials": "{n} tentativas",
        "cards": (
            (
                "PILOTO",
                "Um registro assinado e\npúblico muda as afirmações?",
                "Nenhum efeito neste tamanho.\nA medida era quase artefato.",
            ),
            (
                "ESTUDO 1",
                "Registro publicado contra\num mantido em privado",
                "Nenhum efeito detectável\nda publicidade.",
            ),
            (
                "ESTUDO 2",
                "Registro de afirmações com\nevidência contra nenhum",
                'Diz "completo" metade das\nvezes. Mesmo trabalho.',
            ),
            (
                "ESTUDO 3",
                "Instrução, pressão e\ntestes de aceitação",
                "Nenhum braço mostrou\nganho nos cinco testes.",
            ),
        ),
        "fig": {
            "Pilot · public − private · unbacked claims": (
                "Piloto · público − privado · afirmações sem respaldo"
            ),
            "Study 1 · public − private · false completion (valid task)": (
                "Estudo 1 · público − privado · falsa conclusão (tarefa válida)"
            ),
            "Study 2 · record − no record · false completion": (
                "Estudo 2 · registro − sem registro · falsa conclusão"
            ),
            "Study 2 · record − no record · false non-completion": (
                "Estudo 2 · registro − sem registro · falsa não conclusão"
            ),
            "Study 3 · instruction only − record · false completion*": (
                "Estudo 3 · só instrução − registro · falsa conclusão*"
            ),
            "Study 3 · pressure − record · false completion": (
                "Estudo 3 · pressão − registro · falsa conclusão"
            ),
            "Study 3 · acceptance tests − record · pass rate": (
                "Estudo 3 · testes de aceitação − registro · taxa de aprovação"
            ),
            "difference in percentage points (95% interval)": (
                "diferença em pontos percentuais (intervalo de 95%)"
            ),
            "What each treatment changed": "O que cada tratamento mudou",
            "* measurement-limited: the labeller's agreement differs too much between these two "
            "arms; no claim is made.": (
                "* limitado pela medição: a concordância do rotulador difere demais entre esses "
                "dois braços; nenhuma afirmação é feita."
            ),
            "No record tool": "Sem ferramenta de registro",
            "Record with evidence": "Registro com evidência",
            "% of trials": "% das tentativas",
            'Study 2: similar pass rate, fewer "complete" claims': (
                'Estudo 2: taxa de aprovação parecida, menos afirmações de "completo"'
            ),
            "work passed the hidden check": "o trabalho passou na verificação oculta",
            'agent said "complete"': 'o agente disse "completo"',
            "all 160": "todas as 160",
            "labeller agreement, %": "concordância do rotulador, %",
            "Study 3: the labeller against three model raters (no human rater)": (
                "Estudo 3: o rotulador contra três modelos avaliadores (nenhum avaliador humano)"
            ),
            "to": "a",
        },
    },
    "es": {
        "dec": ",",
        "rtl": False,
        "title": ("Registros de afirmaciones", "y lo que dice un agente de programación"),
        "thesis": "Cambió lo que dijo el agente. No cambió el trabajo.",
        "sub": "Cuatro experimentos · {total} ensayos · comprobaciones ocultas",
        "did": "hizo el trabajo",
        "said": 'dijo "completo"',
        "bars": "estudio 2, agentes con el registro",
        "trials": "{n} ensayos",
        "cards": (
            (
                "PILOTO",
                "¿Un registro firmado y\npúblico cambia las afirmaciones?",
                "Ningún efecto con este tamaño.\nLa medida era casi artefacto.",
            ),
            (
                "ESTUDIO 1",
                "Registro publicado frente\na uno guardado en privado",
                "Ningún efecto detectable\nde la publicidad.",
            ),
            (
                "ESTUDIO 2",
                "Registro de afirmaciones con\nevidencia frente a ninguno",
                'Dice "completo" la mitad\nde veces. Mismo trabajo.',
            ),
            (
                "ESTUDIO 3",
                "Instrucción, presión y\npruebas de aceptación",
                "Ningún brazo mostró\nganancia en las cinco pruebas.",
            ),
        ),
        "fig": {
            "Pilot · public − private · unbacked claims": (
                "Piloto · público − privado · afirmaciones sin respaldo"
            ),
            "Study 1 · public − private · false completion (valid task)": (
                "Estudio 1 · público − privado · falsa finalización (tarea válida)"
            ),
            "Study 2 · record − no record · false completion": (
                "Estudio 2 · registro − sin registro · falsa finalización"
            ),
            "Study 2 · record − no record · false non-completion": (
                "Estudio 2 · registro − sin registro · falsa no finalización"
            ),
            "Study 3 · instruction only − record · false completion*": (
                "Estudio 3 · solo instrucción − registro · falsa finalización*"
            ),
            "Study 3 · pressure − record · false completion": (
                "Estudio 3 · presión − registro · falsa finalización"
            ),
            "Study 3 · acceptance tests − record · pass rate": (
                "Estudio 3 · pruebas de aceptación − registro · tasa de aprobación"
            ),
            "difference in percentage points (95% interval)": (
                "diferencia en puntos porcentuales (intervalo del 95%)"
            ),
            "What each treatment changed": "Qué cambió cada tratamiento",
            "* measurement-limited: the labeller's agreement differs too much between these two "
            "arms; no claim is made.": (
                "* limitado por la medición: la concordancia del etiquetador difiere demasiado "
                "entre estos dos brazos; no se afirma nada."
            ),
            "No record tool": "Sin herramienta de registro",
            "Record with evidence": "Registro con evidencia",
            "% of trials": "% de los ensayos",
            'Study 2: similar pass rate, fewer "complete" claims': (
                'Estudio 2: tasa de aprobación parecida, menos afirmaciones de "completo"'
            ),
            "work passed the hidden check": "el trabajo pasó la comprobación oculta",
            'agent said "complete"': 'el agente dijo "completo"',
            "all 160": "las 160",
            "labeller agreement, %": "concordancia del etiquetador, %",
            "Study 3: the labeller against three model raters (no human rater)": (
                "Estudio 3: el etiquetador frente a tres modelos evaluadores "
                "(ningún evaluador humano)"
            ),
            "to": "a",
        },
    },
    "it": {
        "dec": ",",
        "rtl": False,
        "title": ("Registri di affermazioni", "e ciò che dice un agente di programmazione"),
        "thesis": "Ha cambiato ciò che l'agente ha detto. Non ha cambiato il lavoro.",
        "sub": "Quattro esperimenti · {total} prove · verifiche nascoste",
        "did": "ha fatto il lavoro",
        "said": 'ha detto "completo"',
        "bars": "studio 2, agenti con il registro",
        "trials": "{n} prove",
        "cards": (
            (
                "PILOTA",
                "Un registro firmato e\npubblico cambia le affermazioni?",
                "Nessun effetto a questa\ndimensione. Misura quasi artefatto.",
            ),
            (
                "STUDIO 1",
                "Registro pubblicato contro\nuno tenuto privato",
                "Nessun effetto rilevabile\ndella pubblicità.",
            ),
            (
                "STUDIO 2",
                "Registro delle affermazioni\ncon prove contro nessuno",
                'Dice "completo" la metà\ndelle volte. Stesso lavoro.',
            ),
            (
                "STUDIO 3",
                "Istruzione, pressione e\ntest di accettazione",
                "Nessun braccio ha mostrato\nun guadagno nei cinque test.",
            ),
        ),
        "fig": {
            "Pilot · public − private · unbacked claims": (
                "Pilota · pubblico − privato · affermazioni senza riscontro"
            ),
            "Study 1 · public − private · false completion (valid task)": (
                "Studio 1 · pubblico − privato · falso completamento (compito valido)"
            ),
            "Study 2 · record − no record · false completion": (
                "Studio 2 · registro − nessun registro · falso completamento"
            ),
            "Study 2 · record − no record · false non-completion": (
                "Studio 2 · registro − nessun registro · falso non completamento"
            ),
            "Study 3 · instruction only − record · false completion*": (
                "Studio 3 · sola istruzione − registro · falso completamento*"
            ),
            "Study 3 · pressure − record · false completion": (
                "Studio 3 · pressione − registro · falso completamento"
            ),
            "Study 3 · acceptance tests − record · pass rate": (
                "Studio 3 · test di accettazione − registro · tasso di superamento"
            ),
            "difference in percentage points (95% interval)": (
                "differenza in punti percentuali (intervallo al 95%)"
            ),
            "What each treatment changed": "Che cosa ha cambiato ogni trattamento",
            "* measurement-limited: the labeller's agreement differs too much between these two "
            "arms; no claim is made.": (
                "* limitato dalla misurazione: la concordanza dell'etichettatore differisce troppo "
                "tra questi due bracci; non si afferma nulla."
            ),
            "No record tool": "Nessuno strumento di registro",
            "Record with evidence": "Registro con prove",
            "% of trials": "% delle prove",
            'Study 2: similar pass rate, fewer "complete" claims': (
                'Studio 2: tasso di superamento simile, meno affermazioni di "completo"'
            ),
            "work passed the hidden check": "il lavoro ha superato la verifica nascosta",
            'agent said "complete"': 'l\'agente ha detto "completo"',
            "all 160": "tutte le 160",
            "labeller agreement, %": "concordanza dell'etichettatore, %",
            "Study 3: the labeller against three model raters (no human rater)": (
                "Studio 3: l'etichettatore contro tre modelli valutatori (nessun valutatore umano)"
            ),
            "to": "a",
        },
    },
    "he": {
        "dec": ".",
        "rtl": True,
        "title": ("רישומי טענות", "ומה שסוכן תכנות אומר"),
        "thesis": "זה שינה את מה שהסוכן אמר. זה לא שינה את העבודה.",
        "sub": "ארבעה ניסויים · {total} הרצות · בדיקות נסתרות",
        "did": "ביצע את העבודה",
        "said": 'אמר "הושלם"',
        "bars": "מחקר 2, סוכנים עם הרישום",
        "trials": "{n} הרצות",
        "cards": (
            (
                "פיילוט",
                "האם רישום חתום ופומבי\nמשנה את הטענות?",
                "אין אפקט בגודל זה. המדד\nהיה ברובו תוצר מדידה.",
            ),
            (
                "מחקר 1",
                "רישום פומבי מול\nרישום שנשמר בפרטיות",
                "אין אפקט ניתן לזיהוי\nשל הפומביות.",
            ),
            (
                "מחקר 2",
                "רישום טענות עם ראיות\nמול היעדר רישום",
                'אומר "הושלם" בחצי\nמהפעמים. אותה עבודה.',
            ),
            (
                "מחקר 3",
                "הנחיה, לחץ\nובדיקות קבלה",
                "אף זרוע לא הראתה\nשיפור בחמשת המבחנים.",
            ),
        ),
        "fig": {
            "Pilot · public − private · unbacked claims": "פיילוט · פומבי − פרטי · טענות לא מגובות",
            "Study 1 · public − private · false completion (valid task)": (
                "מחקר 1 · פומבי − פרטי · השלמה כוזבת (משימה תקפה)"
            ),
            "Study 2 · record − no record · false completion": (
                "מחקר 2 · רישום − ללא רישום · השלמה כוזבת"
            ),
            "Study 2 · record − no record · false non-completion": (
                "מחקר 2 · רישום − ללא רישום · אי-השלמה כוזבת"
            ),
            "Study 3 · instruction only − record · false completion*": (
                "מחקר 3 · הנחיה בלבד − רישום · השלמה כוזבת*"
            ),
            "Study 3 · pressure − record · false completion": "מחקר 3 · לחץ − רישום · השלמה כוזבת",
            "Study 3 · acceptance tests − record · pass rate": (
                "מחקר 3 · בדיקות קבלה − רישום · שיעור מעבר"
            ),
            "difference in percentage points (95% interval)": "הפרש בנקודות אחוז (רווח סמך 95%)",
            "What each treatment changed": "מה כל טיפול שינה",
            "* measurement-limited: the labeller's agreement differs too much between these two "
            "arms; no claim is made.": (
                "* מוגבל מדידה: הסכמת המתייג שונה מדי בין שתי הזרועות האלה; לא נטענת טענה."
            ),
            "No record tool": "ללא כלי רישום",
            "Record with evidence": "רישום עם ראיות",
            "% of trials": "% מההרצות",
            'Study 2: similar pass rate, fewer "complete" claims': (
                'מחקר 2: שיעור מעבר דומה, פחות טענות "הושלם"'
            ),
            "work passed the hidden check": "העבודה עברה את הבדיקה הנסתרת",
            'agent said "complete"': 'הסוכן אמר "הושלם"',
            "all 160": "כל 160",
            "labeller agreement, %": "הסכמת המתייג, %",
            "Study 3: the labeller against three model raters (no human rater)": (
                "מחקר 3: המתייג מול שלושה מודלים מעריכים (ללא מעריך אנושי)"
            ),
            "to": "עד",
        },
    },
}
# Figure text that is the same in every language: arm codes and rater names.
SAME = {"S", "I", "K", "TD", "Fable", "Grok", "Hydrogen"}
INTERVAL = re.compile(r"^([+−]\d+\.\d)  \(([+−]\d+\.\d) to ([+−]\d+\.\d)\)$")
NUMERIC = re.compile(r"^[\d.%/\n]+$")


def number(value, lang):
    """Write a number in the format of one language.

    Parameters
    ----------
    value : str
        The number as English writes it (``,`` for thousands, ``.`` for decimals).
    lang : str
        Language key of ``LANGS``.

    Returns
    -------
    str
        The same number with the language's separators.
    """
    if LANGS[lang]["dec"] == ".":
        return value
    return value.translate(str.maketrans({",": ".", ".": ","}))


def count(name):
    """Count the trials in one per-trial score file.

    Parameters
    ----------
    name : str
        File name under ``runs/`` without the ``.csv`` extension.

    Returns
    -------
    int
        Number of data rows.
    """
    with (RUNS / f"{name}.csv").open() as f:
        return sum(1 for _ in csv.DictReader(f))


class Canvas:
    """A figure whose axes span the whole canvas in points, drawn from the left or the right.

    With ``rtl`` true every x coordinate is mirrored (``x -> width - x``) and the horizontal
    alignment flips, so one layout serves Hebrew too.

    Parameters
    ----------
    width, height : int
        Canvas size in points (one unit is one point, so font sizes share the scale).
    color : str
        Background colour.
    rtl : bool
        Draw mirrored, right to left.
    """

    def __init__(self, width, height, color, rtl=False):
        """Create the figure and its full-canvas axes (see the class docstring)."""
        self.fig = plt.figure(figsize=(width / 72, height / 72), facecolor=color)
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.axis("off")
        self.width, self.rtl = width, rtl

    def box(self, x, y, w, h, radius, **kw):
        """Draw a rounded rectangle, mirrored when ``rtl``.

        Parameters
        ----------
        x, y : float
            Lower-left corner in the left-to-right layout.
        w, h : float
            Width and height.
        radius : float
            Corner radius.
        **kw
            Passed to ``FancyBboxPatch``.
        """
        x = self.width - x - w if self.rtl else x
        style = f"round,pad=0,rounding_size={radius}"
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, **kw))

    def text(self, x, y, s, maxw=None, ha="left", **kw):
        """Write ``s`` at (x, y); shrink the font if it is wider than ``maxw`` points.

        Parameters
        ----------
        x, y : float
            Anchor point in the left-to-right layout.
        s : str
            Text.
        maxw : float, optional
            Maximum width in points; translations differ in length and must not overflow.
        ha : str
            Horizontal alignment (``left``, ``right`` or ``center``), flipped when ``rtl``.
        **kw
            Passed to ``Axes.text``.
        """
        if self.rtl:
            x, ha = self.width - x, {"left": "right", "right": "left"}.get(ha, ha)
        t = self.ax.text(x, y, s, ha=ha, **kw)
        if maxw:
            width = t.get_window_extent(self.fig.canvas.get_renderer()).width * 72 / self.fig.dpi
            if width > maxw:
                t.set_fontsize(t.get_fontsize() * maxw / width * 0.98)

    def line(self, x0, x1, y, **kw):
        """Draw a horizontal line from ``x0`` to ``x1``, mirrored when ``rtl``.

        Parameters
        ----------
        x0, x1 : float
            Ends in the left-to-right layout.
        y : float
            Height.
        **kw
            Passed to ``Axes.plot``.
        """
        if self.rtl:
            x0, x1 = self.width - x0, self.width - x1
        self.ax.plot([x0, x1], [y, y], **kw)

    def arrow(self, x0, x1, y, **kw):
        """Draw an arrow from ``x0`` to ``x1``, mirrored when ``rtl``.

        Parameters
        ----------
        x0, x1 : float
            Tail and head in the left-to-right layout.
        y : float
            Height.
        **kw
            Passed as ``arrowprops``.
        """
        if self.rtl:
            x0, x1 = self.width - x0, self.width - x1
        self.ax.annotate("", (x1, y), (x0, y), arrowprops=kw)

    def save(self, path, color):
        """Write the SVG with no date in its metadata and close the figure.

        Parameters
        ----------
        path : pathlib.Path
            Output file.
        color : str
            Background colour.
        """
        self.fig.savefig(path, facecolor=color, metadata={"Date": None})
        plt.close(self.fig)


def stem(piece, lang, theme):
    """Name one brand picture.

    Parameters
    ----------
    piece : str
        ``banner`` or ``design``.
    lang : str
        Language key of ``LANGS``.
    theme : str
        ``light`` or ``dark``.

    Returns
    -------
    pathlib.Path
        ``<piece>-<theme>.svg`` for English (the name the English README has always used),
        ``<piece>-<lang>-<theme>.svg`` for the others.
    """
    return OUT / (f"{piece}-{theme}.svg" if lang == "en" else f"{piece}-{lang}-{theme}.svg")


def banner(lang, theme, t):
    """Draw the README banner for one language and theme.

    Parameters
    ----------
    lang : str
        Language key of ``LANGS``.
    theme : str
        Theme name, used in the file name.
    t : dict
        Theme colours.
    """
    L = LANGS[lang]
    text = (RUNS / "study2-analysis.txt").read_text()
    passed, n, said = (
        int(x) for x in re.search(r"S: passed (\d+)/(\d+), says complete (\d+)/", text).groups()
    )
    total = number(f"{sum(count(f) for f in SCORES):,}", lang)
    c = Canvas(1280, 320, t["bg"], L["rtl"])
    bold = {"color": t["ink"], "fontsize": 40, "fontweight": "bold"}
    c.text(64, 214, L["title"][0], maxw=830, **bold)
    c.text(64, 158, L["title"][1], maxw=830, **bold)
    c.text(64, 96, L["thesis"], maxw=830, color=t["amber"], fontsize=17)
    c.text(64, 56, L["sub"].format(total=total), maxw=830, color=t["muted"], fontsize=13)
    for y, value, color, label in (
        (196, passed, t["teal"], L["did"]),
        (120, said, t["amber"], L["said"]),
    ):
        c.box(930, y, 286, 34, 6, fc=t["line"], ec="none")
        c.box(930, y, 286 * value / n, 34, 6, fc=color, ec="none")
        c.text(
            930, y + 46, f"{label} · {100 * value / n:.0f}%", maxw=300, color=t["ink"], fontsize=14
        )
    c.text(930, 84, L["bars"], maxw=300, color=t["muted"], fontsize=12)
    c.save(stem("banner", lang, theme), t["bg"])


def design(lang, theme, t):
    """Draw the four experiments as a row of cards for one language and theme.

    Parameters
    ----------
    lang : str
        Language key of ``LANGS``.
    theme : str
        Theme name, used in the file name.
    t : dict
        Theme colours.
    """
    L = LANGS[lang]
    c = Canvas(1280, 300, t["bg"], L["rtl"])
    for i, ((tag, question, answer), name) in enumerate(zip(L["cards"], SCORES, strict=True)):
        x = 40 + i * 305
        edge = t["amber"] if i == 2 else t["line"]
        c.box(x, 30, 285, 240, 12, fc=t["card"], ec=edge, lw=1.6)
        c.text(x + 22, 232, tag, maxw=130, color=t["amber"], fontsize=13, fontweight="bold")
        trials = L["trials"].format(n=number(f"{count(name):,}", lang))
        c.text(x + 263, 232, trials, maxw=110, color=t["muted"], fontsize=12, ha="right")
        c.text(
            x + 22,
            170,
            question,
            maxw=245,
            color=t["ink"],
            fontsize=15,
            fontweight="bold",
            linespacing=1.35,
        )
        c.line(x + 22, x + 263, 140, color=t["line"], lw=1)
        c.text(x + 22, 72, answer, maxw=245, color=t["muted"], fontsize=14, linespacing=1.4)
        if i < 3:
            c.arrow(x + 287, x + 303, 150, arrowstyle="-|>", color=t["muted"])
    c.save(stem("design", lang, theme), t["bg"])


def translate(s, lang):
    """Translate one piece of figure text, or stop if no translation is known.

    Parameters
    ----------
    s : str
        English text drawn by ``scripts/make_figures.py``.
    lang : str
        Language key of ``LANGS`` (not ``en``).

    Returns
    -------
    str
        The text in that language, numbers in its format.

    Raises
    ------
    KeyError
        If ``s`` is neither a number, an arm or rater name, nor a key of the language's table.
    """
    fig = LANGS[lang]["fig"]
    if s in SAME:
        return s
    if NUMERIC.match(s) or re.match(r"^[+−]?\d+$", s):
        return number(s, lang)
    m = INTERVAL.match(s)
    if m:
        d, lo, hi = (number(v, lang) for v in m.groups())
        if LANGS[lang]["rtl"]:  # isolate each signed number, or bidi puts its sign after it
            d, lo, hi = (
                f"\N{LEFT-TO-RIGHT ISOLATE}{v}\N{POP DIRECTIONAL ISOLATE}" for v in (d, lo, hi)
            )
        return f"{d}  ({lo} {fig['to']} {hi})"
    return fig[s]


def figures(lang):
    """Draw the three Results figures in one language, both themes, as PNG and SVG.

    The sealed ``scripts/make_figures.py`` is imported unchanged and draws each figure; its
    ``save`` is replaced by one that translates every text artist and writes under
    ``assets/figures/``.

    Parameters
    ----------
    lang : str
        Language key of ``LANGS`` (not ``en``).
    """
    sys.dont_write_bytecode = True  # nothing may be written into the sealed scripts/ folder
    spec = importlib.util.spec_from_file_location(
        "make_figures", ROOT / "scripts" / "make_figures.py"
    )
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    FIGURES.mkdir(exist_ok=True)

    def save(fig, name):
        """Translate every text of ``fig`` and write it in both formats.

        Parameters
        ----------
        fig : matplotlib.figure.Figure
            The figure drawn by the sealed script.
        name : str
            Figure name without extension.
        """
        # Category labels (bars, arms) are drawn again from the axis when the figure is saved, so
        # they are replaced on the axis; numeric tick labels are still empty here and stay numbers.
        for ax in fig.axes:
            for axis in (ax.xaxis, ax.yaxis):
                labels = [label.get_text() for label in axis.get_ticklabels()]
                if any(s in LANGS[lang]["fig"] for s in labels):
                    view = axis.get_view_interval()
                    axis.set_ticks(axis.get_ticklocs(), [translate(s, lang) for s in labels])
                    axis.set_view_interval(*view, ignore=True)
        done = set(LANGS[lang]["fig"].values())  # the category labels just translated
        for artist in fig.findobj(Text):
            if artist.get_text() and artist.get_text() not in done:
                artist.set_text(translate(artist.get_text(), lang))
        theme = "dark" if mf.SUFFIX == "-dark" else "light"
        for ext in ("png", "svg"):
            fig.savefig(
                FIGURES / f"{name}-{lang}-{theme}.{ext}",
                bbox_inches="tight",
                facecolor=mf.BG,
                metadata={"Date": None},
            )
        plt.close(fig)

    mf.save = save
    for suffix in mf.THEMES:
        mf.use(suffix)
        plt.rcParams["svg.hashsalt"] = "eilikrineia"
        mf.fig1_effects()
        mf.fig2_said_vs_did()
        mf.fig3_labeller_audit()


def dark_lockup():
    """Derive ``lab-lockup-dark.png`` from the original: the black strokes take the dark ink."""
    from PIL import Image  # a dependency of matplotlib

    light = Image.open(OUT / "lab-lockup-light.png").convert("RGBA")
    r, g, b = (int(THEMES["dark"]["ink"][i : i + 2], 16) for i in (1, 3, 5))
    dark = Image.new("RGBA", light.size, (r, g, b, 0))
    dark.putalpha(light.getchannel("A"))
    dark.save(OUT / "lab-lockup-dark.png", optimize=True)


if __name__ == "__main__":
    for language in LANGS:
        for theme, colours in THEMES.items():
            banner(language, theme, colours)
            design(language, theme, colours)
        if language != "en":
            figures(language)
    dark_lockup()
    print(f"{len(LANGS) * 4} brand pictures -> {OUT}; {(len(LANGS) - 1) * 12} figures -> {FIGURES}")
