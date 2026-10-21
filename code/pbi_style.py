"""
pbi_style.py - Shared chart style that follows Microsoft Power BI's default report look.

PLAIN-LANGUAGE NOTE: Every chart in the project imports this file, so they all look
like Power BI visuals: Power BI's default theme colors, a Segoe UI-style font
(Selawik, Microsoft's open-licensed stand-in for Segoe UI, in code/fonts/),
a bold title at top left, a dot legend under the title, faint horizontal
gridlines, no axis lines, and values labeled at the end of each line.
The matching Power BI theme file is powerbi/rural_road_panel_theme.json.
"""
import os

import matplotlib
from matplotlib import font_manager

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
for f in os.listdir(FONT_DIR):
    if f.endswith(".ttf"):
        font_manager.fontManager.addfont(os.path.join(FONT_DIR, f))

# Power BI default theme ("Default", 2023+) data colors, in order; the first two
# pass the colorblind-separation check as a pair and are the only ones paired here.
BLUE, ORANGE = "#118DFF", "#E66C37"
NAVY = "#12239E"
TITLE, LABEL, MUTED, GRID, BORDER, PAGE = "#252423", "#605E5C", "#A19F9D", "#E1DFDD", "#E1DFDD", "#FFFFFF"
# sequential ramp for maps, light to dark, ending in Power BI's dark blue
SEQ = ["#DCEEFF", "#B3DAFF", "#7DBFFF", "#3FA0FF", "#118DFF", "#0B5FC4", "#12239E"]


def apply(base_size=9):
    plt.rcParams.update({
        "font.family": "Selawik", "font.size": base_size,
        "axes.titlesize": base_size + 3, "axes.labelsize": base_size, "axes.labelcolor": LABEL,
        "xtick.color": LABEL, "ytick.color": LABEL, "xtick.labelsize": base_size - 0.5, "ytick.labelsize": base_size - 0.5,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.edgecolor": GRID, "axes.facecolor": PAGE, "figure.facecolor": PAGE, "savefig.facecolor": PAGE,
        "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 5, "ytick.major.pad": 6,
        "legend.fontsize": base_size - 0.5, "legend.frameon": False, "legend.handlelength": 0.8,
        "lines.linewidth": 2.2, "savefig.dpi": 220,
    })


def gridlines(ax):
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.spines["bottom"].set_color(GRID)


def dot_legend(ax, items, y=1.02, fig_level=None):
    """Power BI legend: colored dots + labels in one row above the plot."""
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", ms=6, color=c, label=l) for l, c in items]
    target = fig_level or ax
    kw = dict(handles=h, ncol=len(items), loc="lower left", handletextpad=0.5, columnspacing=1.4, borderaxespad=0)
    if fig_level is None:
        kw["bbox_to_anchor"] = (0, y)
    return target.legend(**kw)


def title(fig, text, subtitle=None, x=0.02):
    h = fig.get_size_inches()[1]
    fig.text(x, 1 - 0.14 / h, text, ha="left", va="top", fontsize=13, fontweight="bold", color=TITLE)
    if subtitle:
        fig.text(x, 1 - 0.42 / h, subtitle, ha="left", va="top", fontsize=9, color=LABEL)


def end_label(ax, x, y, text, color, dy=0):
    ax.annotate(text, (x, y), xytext=(6, dy), textcoords="offset points", va="center", fontsize=9,
                color=TITLE, fontweight="bold")


def thousands(ax):
    def fmt(v, _):
        if v >= 1000:
            t = f"{v / 1000:.2f}".rstrip("0").rstrip(".")
            return t + "K"
        return f"{v:.0f}"
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(fmt))
