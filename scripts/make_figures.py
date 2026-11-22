"""Figures as code. Every number is read from the frozen files under ``runs/``; none is typed here.

Claim map (no figure without a claim)
-------------------------------------
- ``fig1_effects``: across the four experiments, no treatment moved false completion or finished
  work in the hoped direction except recording with evidence (study 2), whose gain on false
  completion came with a larger rise in false non-completion.
- ``fig2_said_vs_did``: in study 2 the share of finished work is the same with and without the
  record, while the share of agents that say "complete" halves.
- ``fig3_labeller_audit``: the automatic labeller agrees with three model raters on 73% to 79% of
  160 audited messages, and the arm it reads worst depends on the rater.

Usage
-----
    python scripts/make_figures.py        # writes PNG and SVG to output/figures/
"""

import csv
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUNS, OUT = ROOT / "runs", ROOT / "output" / "figures"
TITLES = True  # the paper edition (--paper DIR) carries the title in its caption instead
THEMES = {
    "": {
        "BG": "#FFFFFF",
        "INK": "#0B1B2B",
        "MUTED": "#5B6B7B",
        "GRID": "#E3E8EE",
        "AMBER": "#B86E00",
        "TEAL": "#0F766E",
        "RED": "#B42318",
    },
    "-dark": {
        "BG": "#0D1117",
        "INK": "#E6EDF3",
        "MUTED": "#9BA7B4",
        "GRID": "#30363D",
        "AMBER": "#F5A524",
        "TEAL": "#2DD4BF",
        "RED": "#FF7B72",
    },
}
SUFFIX = ""
BG, INK, MUTED, GRID, AMBER, TEAL, RED = THEMES[""].values()
EST = r"([+-]\d+\.\d) (?:points )?\(95% ([+-]\d+\.\d) to ([+-]\d+\.\d)\)"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "svg.fonttype": "path",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.dpi": 200,
    }
)


def use(suffix):
    """Switch the colours of every later figure to one theme.

    Parameters
    ----------
    suffix : str
        ``""`` for the light theme, ``"-dark"`` for the dark one; it is appended to file names.
    """
    global SUFFIX, BG, INK, MUTED, GRID, AMBER, TEAL, RED
    SUFFIX = suffix
    BG, INK, MUTED, GRID, AMBER, TEAL, RED = THEMES[suffix].values()
    plt.rcParams.update(
        {
            "axes.edgecolor": GRID,
            "axes.facecolor": BG,
            "figure.facecolor": BG,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
        }
    )


def estimate(name, section, prefix):
    """Read one "difference (95% lo to hi)" triple from a frozen analysis output.

    Parameters
    ----------
    name : str
        File name under ``runs/``.
    section : str
        Text that opens the section to search in (empty string for the whole file).
    prefix : str
        Text that starts the wanted line inside that section.

    Returns
    -------
    tuple of float
        ``(difference, low, high)`` in percentage points.
    """
    text = (RUNS / name).read_text()
    text = text[text.index(section) :] if section else text
    line = next(x for x in text.splitlines() if x.strip().startswith(prefix))
    return tuple(float(v) for v in re.search(EST, line).groups())


def title(ax, text, **kw):
    """Set the title of a figure, unless the titles are switched off for the paper edition.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to title.
    text : str
        The title.
    **kw
        Passed to ``Axes.set_title``.
    """
    if TITLES:
        ax.set_title(text, loc="left", color=INK, fontweight="bold", **kw)


def save(fig, stem):
    """Write one figure as PNG and SVG.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to write.
    stem : str
        File name without extension.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(
            OUT / f"{stem}{SUFFIX}.{ext}",
            bbox_inches="tight",
            facecolor=BG,
            metadata={"Date": None},
        )
    plt.close(fig)


def fig1_effects():
    """Draw every main contrast of the four experiments as a difference with its 95% interval."""
    rows = [
        (
            "Pilot · public − private · unbacked claims",
            estimate("pilot-analysis.txt", "", "P-S M1"),
            MUTED,
        ),
        (
            "Study 1 · public − private · false completion (valid task)",
            estimate("study-check-validity.txt", "", "text-template-engine only"),
            MUTED,
        ),
        (
            "Study 2 · record − no record · false completion",
            estimate("study2-analysis.txt", "== false_completion", "MH S-control"),
            TEAL,
        ),
        (
            "Study 2 · record − no record · false non-completion",
            estimate("study2-analysis.txt", "== false_non_completion", "MH S-control"),
            RED,
        ),
        (
            "Study 3 · instruction only − record · false completion*",
            estimate("study3-analysis.txt", "== false_completion", "I-S CONFIRMATORY"),
            MUTED,
        ),
        (
            "Study 3 · pressure − record · false completion",
            estimate("study3-analysis.txt", "== false_completion", "K-S CONFIRMATORY"),
            MUTED,
        ),
        (
            "Study 3 · acceptance tests − record · pass rate",
            estimate("study3-analysis.txt", "== passed", "TD-S CONFIRMATORY"),
            MUTED,
        ),
    ]
    # the paper prints this at 14 cm: narrower canvas, each label above its line
    fig, ax = plt.subplots(figsize=(9.6, 4.2) if TITLES else (6.6, 5.2))
    for y, (label, (d, lo, hi), color) in enumerate(reversed(rows)):
        ax.plot([lo, hi], [y, y], color=color, lw=2.2, solid_capstyle="round")
        ax.plot([d], [y], "o", color=color, ms=7)
        ax.text(
            max(hi, 0) + 1.2,
            y,
            f"{d:+.1f}  ({lo:+.1f} to {hi:+.1f})".replace("-", "\N{MINUS SIGN}"),
            va="center",
            color=INK,
            fontsize=9,
        )
        if TITLES:
            ax.text(-19, y, label, va="center", ha="right", color=INK)
        else:
            ax.text(
                -17.5,
                y + 0.36,
                label,
                va="center",
                ha="left",
                color=INK,
                fontsize=9.5,
                zorder=5,
                bbox={"facecolor": fig.get_facecolor(), "edgecolor": "none", "pad": 1.5},
            )
    ax.axvline(0, color=INK, lw=1)
    ax.set_xlim(-18, 46 if TITLES else 52)
    ax.set_ylim(-0.7, len(rows) - (0.3 if TITLES else 0.1))
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("difference in percentage points (95% interval)", color=MUTED)
    ax.tick_params(colors=MUTED)
    title(ax, "What each treatment changed", x=-0.92)
    if TITLES:  # the paper carries this sentence in the figure note, at text size
        fig.text(
            0.02,
            -0.03,
            "* measurement-limited: the labeller's agreement differs too much between these two "
            "arms; no claim is made.",
            color=MUTED,
            fontsize=8,
        )
    save(fig, "fig1_effects")


def fig2_said_vs_did():
    """Draw, for study 2, the share that passed next to the share that said "complete"."""
    text = (RUNS / "study2-analysis.txt").read_text()
    got = {
        arm: [
            int(x)
            for x in re.search(rf"{arm}: passed (\d+)/(\d+), says complete (\d+)/", text).groups()
        ]
        for arm in ("S", "control")
    }
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    names = {"control": "No record tool", "S": "Record with evidence"}
    for i, arm in enumerate(("control", "S")):
        passed, n, said = got[arm]
        for j, (value, color, what) in enumerate(
            ((passed, TEAL, "work passed the hidden check"), (said, AMBER, 'agent said "complete"'))
        ):
            x = i + (j - 0.5) * 0.36
            ax.bar(x, 100 * value / n, 0.32, color=color, label=what if i == 0 else None)
            ax.text(
                x,
                100 * value / n + 1.5,
                f"{100 * value / n:.1f}%\n{value}/{n}",
                ha="center",
                fontsize=8.5,
                color=INK,
            )
    ax.set_xticks([0, 1], [names["control"], names["S"]])
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of trials", color=MUTED)
    ax.tick_params(colors=MUTED)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=2, fontsize=9)
    title(ax, 'Study 2: similar pass rate, fewer "complete" claims', y=1.2)
    save(fig, "fig2_said_vs_did")


def fig3_labeller_audit():
    """Draw the labeller's agreement with each model rater, overall and per arm."""
    key = {r["id"]: r for r in map(json.loads, (RUNS / "study3-audit" / "key.jsonl").open())}
    arms, raters = (
        ["all", "S", "I", "K", "TD"],
        [("fable", MUTED), ("grok", AMBER), ("hydrogen", TEAL)],
    )
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    for j, (rater, color) in enumerate(raters):
        lab = {
            int(k): v["label"]
            for k, v in json.loads((RUNS / "study3-audit" / f"{rater}.json").read_text()).items()
        }
        for i, arm in enumerate(arms):
            ids = [k for k, v in key.items() if arm in ("all", v["arm"])]
            acc = (
                100
                * sum((key[k]["labeller"] == "complete") == (lab[k] == "complete") for k in ids)
                / len(ids)
            )
            x = i + (j - 1) * 0.26
            ax.bar(x, acc, 0.24, color=color, label=rater.capitalize() if i == 0 else None)
            ax.text(x, acc + 1, f"{acc:.1f}", ha="center", fontsize=7, color=INK)
    ax.axhline(50, color=GRID, lw=1)
    ax.set_xticks(range(len(arms)), ["all 160", "S", "I", "K", "TD"])
    ax.set_ylim(0, 100)
    ax.set_ylabel("labeller agreement, %", color=MUTED)
    ax.tick_params(colors=MUTED)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.18), fontsize=9)
    title(
        ax,
        "Study 3: the labeller against three model raters (no human rater)",
        y=1.18,
        fontsize=10,
    )
    save(fig, "fig3_labeller_audit")


def trial_total():
    """Count the trials in the four per-trial score files.

    Returns
    -------
    int
        Number of trials across the pilot and the three studies.
    """
    files = ("pilot-scores", "study-scores", "study2-scores", "study3-scores")
    return sum(sum(1 for _ in csv.DictReader((RUNS / f"{f}.csv").open())) for f in files)


if __name__ == "__main__":
    if "--paper" in sys.argv:  # light theme only, no titles, into the folder given
        OUT, TITLES, THEMES = Path(sys.argv[sys.argv.index("--paper") + 1]), False, {"": THEMES[""]}
    for theme in THEMES:
        use(theme)
        fig1_effects()
        fig2_said_vs_did()
        fig3_labeller_audit()
    print(f"3 figures -> {OUT} ({trial_total()} trials)")
