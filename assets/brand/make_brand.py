"""Brand pictures drawn as code: the README banner and the design diagram, light and dark.

Claim map (no picture without a claim)
--------------------------------------
- ``banner-{light,dark}.svg``: the title and the thesis. The two bars are study 2's measured
  shares for the arm with the record: work that passed the hidden check and agents that said
  "complete". They are read from ``runs/study2-analysis.txt``.
- ``design-{light,dark}.svg``: the four experiments, what each compared and how many trials
  each ran. Trial counts are read from the per-trial score files.

Text is converted to outlines, so the pictures look the same without any installed font.

Usage
-----
    python assets/brand/make_brand.py
"""

import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent
RUNS = OUT.parents[1] / "runs"
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
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path"})


def canvas(width, height, color):
    """Create a figure whose axes span the whole canvas in pixel-like units.

    Parameters
    ----------
    width, height : int
        Canvas size in points (one unit is one point, so font sizes share the scale).
    color : str
        Background colour.

    Returns
    -------
    tuple
        ``(figure, axes)``.
    """
    fig = plt.figure(figsize=(width / 72, height / 72), facecolor=color)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.axis("off")
    return fig, ax


def banner(name, t):
    """Draw the README banner for one theme.

    Parameters
    ----------
    name : str
        Theme name, used in the file name.
    t : dict
        Theme colours.
    """
    text = (RUNS / "study2-analysis.txt").read_text()
    passed, n, said = (
        int(x) for x in re.search(r"S: passed (\d+)/(\d+), says complete (\d+)/", text).groups()
    )
    names = ("pilot-scores", "study-scores", "study2-scores", "study3-scores")
    total = sum(sum(1 for _ in csv.DictReader((RUNS / f"{f}.csv").open())) for f in names)
    fig, ax = canvas(1280, 320, t["bg"])
    ax.text(64, 214, "Claim records", color=t["ink"], fontsize=40, fontweight="bold")
    ax.text(64, 158, "and what a coding agent says", color=t["ink"], fontsize=40, fontweight="bold")
    ax.text(
        64,
        96,
        "It changed what the agent said. It did not change the work.",
        color=t["amber"],
        fontsize=17,
    )
    ax.text(
        64,
        56,
        f"Four experiments · {total:,} trials · hidden checks",
        color=t["muted"],
        fontsize=13,
    )
    for y, value, color, label in (
        (196, passed, t["teal"], "did the work"),
        (120, said, t["amber"], 'said "complete"'),
    ):
        ax.add_patch(
            FancyBboxPatch(
                (930, y), 286, 34, boxstyle="round,pad=0,rounding_size=6", fc=t["line"], ec="none"
            )
        )
        width = 286 * value / n
        ax.add_patch(
            FancyBboxPatch(
                (930, y), width, 34, boxstyle="round,pad=0,rounding_size=6", fc=color, ec="none"
            )
        )
        ax.text(930, y + 46, f"{label} · {100 * value / n:.0f}%", color=t["ink"], fontsize=14)
    ax.text(930, 84, "study 2, agents with the record", color=t["muted"], fontsize=12)
    fig.savefig(OUT / f"banner-{name}.svg", facecolor=t["bg"], metadata={"Date": None})
    plt.close(fig)


def design(name, t):
    """Draw the four experiments as a row of cards for one theme.

    Parameters
    ----------
    name : str
        Theme name, used in the file name.
    t : dict
        Theme colours.
    """
    count = {
        f: sum(1 for _ in csv.DictReader((RUNS / f"{f}.csv").open()))
        for f in ("pilot-scores", "study-scores", "study2-scores", "study3-scores")
    }
    cards = [
        (
            "PILOT",
            count["pilot-scores"],
            "Does a signed, public\nrecord change claims?",
            "No effect at this size. The\nmeasure was mostly artefact.",
        ),
        (
            "STUDY 1",
            count["study-scores"],
            "Published record against\na privately kept one",
            "No detectable effect\nof publicity.",
        ),
        (
            "STUDY 2",
            count["study2-scores"],
            "Claim record with evidence\nagainst no record",
            'Says "complete" half as\noften. Same work.',
        ),
        (
            "STUDY 3",
            count["study3-scores"],
            "Instruction, pressure and\nacceptance tests",
            "No arm showed a gain\non five tests.",
        ),
    ]
    fig, ax = canvas(1280, 300, t["bg"])
    for i, (tag, n, question, answer) in enumerate(cards):
        x = 40 + i * 305
        ax.add_patch(
            FancyBboxPatch(
                (x, 30),
                285,
                240,
                boxstyle="round,pad=0,rounding_size=12",
                fc=t["card"],
                ec=t["amber"] if i == 2 else t["line"],
                lw=1.6,
            )
        )
        ax.text(x + 22, 232, tag, color=t["amber"], fontsize=13, fontweight="bold")
        ax.text(x + 263, 232, f"{n:,} trials", color=t["muted"], fontsize=12, ha="right")
        ax.text(
            x + 22, 170, question, color=t["ink"], fontsize=15, fontweight="bold", linespacing=1.35
        )
        ax.plot([x + 22, x + 263], [140, 140], color=t["line"], lw=1)
        ax.text(x + 22, 72, answer, color=t["muted"], fontsize=14, linespacing=1.4)
        if i < 3:
            ax.annotate(
                "",
                (x + 303, 150),
                (x + 287, 150),
                arrowprops={"arrowstyle": "-|>", "color": t["muted"]},
            )
    fig.savefig(OUT / f"design-{name}.svg", facecolor=t["bg"], metadata={"Date": None})
    plt.close(fig)


if __name__ == "__main__":
    for theme, colours in THEMES.items():
        banner(theme, colours)
        design(theme, colours)
    print(f"4 pictures -> {OUT}")
