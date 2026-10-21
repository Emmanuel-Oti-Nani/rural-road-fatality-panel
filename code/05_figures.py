#!/usr/bin/env python3
"""
05_figures.py - Build the release figures (PNG, plus SVG or PDF) in the Power BI style.

PLAIN-LANGUAGE NOTE: Draws four charts from the panel in the look of Power BI
visuals (style shared through code/pbi_style.py). Until the author has verified the
numbers, run without flags and every chart carries a DRAFT stamp; after verification
run `python code/05_figures.py --final`. Output: paper/figures/.
"""
import argparse
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import pbi_style as pbi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
F = os.path.join(ROOT, "paper", "figures")
os.makedirs(F, exist_ok=True)
SRC = "Source: NHTSA FARS 2015-2024 (2024 = Annual Report File); U.S. Census Bureau 2020 urban areas and population estimates."
CREDIT = "Emmanuel Oti Nani, U.S. Rural Road Fatality County Panel (CC BY 4.0)"
pbi.apply(9)


def finish(fig, name, final, source=SRC, exts=("png", "svg")):
    fig.text(0.02, 0.036, source, ha="left", fontsize=7.5, color=pbi.MUTED)
    fig.text(0.02, 0.012, CREDIT, ha="left", fontsize=7.5, color=pbi.MUTED)
    if not final:
        fig.text(0.5, 0.5, "DRAFT", fontsize=70, color="#D64550", alpha=0.12, ha="center", va="center",
                 rotation=25, fontweight="bold")
    # thin card border, like a Power BI visual container
    fig.patches.append(plt.Rectangle((0.003, 0.003), 0.994, 0.994, transform=fig.transFigure, fill=False,
                                     edgecolor=pbi.BORDER, lw=1))
    for ext in exts:
        fig.savefig(os.path.join(F, f"{name}.{ext}"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    w = pd.read_csv(os.path.join(P, "panel_county_year_2015_2024.csv"), dtype={"fips": str, "state_fips": str})
    yrs = sorted(w.year.unique())

    # Figure 1: rural vs urban deaths (Power BI line chart)
    g = w.groupby("year")[["deaths_rural", "deaths_urban"]].sum()
    fig, ax = plt.subplots(figsize=(8, 4.6))
    fig.subplots_adjust(top=0.79, bottom=0.17, left=0.08, right=0.88)
    pbi.title(fig, "Road deaths by location, 2015-2024",
              "Rural = crash location outside a 2020 Census urban area (one fixed map for all years)")
    for col, c, lab, dy in [("deaths_rural", pbi.BLUE, "Rural", -8), ("deaths_urban", pbi.ORANGE, "Urban", 8)]:
        ax.plot(yrs, g[col], color=c, solid_capstyle="round")
        ax.plot(yrs[-1], g[col].iloc[-1], "o", color=c, ms=6, mec="white", mew=1.5)
        pbi.end_label(ax, yrs[-1], g[col].iloc[-1], f"{g[col].iloc[-1]:,}", c, dy)
    ax.set_ylim(0, max(g.max()) * 1.15)
    pbi.thousands(ax)
    ax.set_xticks(yrs)
    ax.set_ylabel("Deaths")
    pbi.gridlines(ax)
    pbi.dot_legend(ax, [("Rural", pbi.BLUE), ("Urban", pbi.ORANGE)])
    finish(fig, "fig1_rural_urban_deaths", a.final)

    # Figure 2: rural share under two definitions (line chart)
    s = w.groupby("year")[["deaths", "deaths_rural", "deaths_fars_rural", "deaths_ru_unknown", "deaths_fars_ru_unknown"]].sum()
    pc = s.deaths_rural / (s.deaths - s.deaths_ru_unknown) * 100
    pf = s.deaths_fars_rural / (s.deaths - s.deaths_fars_ru_unknown) * 100
    fig, ax = plt.subplots(figsize=(8, 4.6))
    fig.subplots_adjust(top=0.79, bottom=0.17, left=0.08, right=0.9)
    pbi.title(fig, "Rural share of road deaths, by definition",
              "Share of deaths with a known location classed as rural")
    for ser, c in [(pc, pbi.BLUE), (pf, pbi.ORANGE)]:
        ax.plot(yrs, ser, color=c)
        ax.plot(yrs[-1], ser.iloc[-1], "o", color=c, ms=6, mec="white", mew=1.5)
        pbi.end_label(ax, yrs[-1], ser.iloc[-1], f"{ser.iloc[-1]:.1f}%", c)
    ax.fill_between(yrs, pf, pc, color=pbi.BLUE, alpha=0.06, lw=0)
    ax.set_ylim(30, 60)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xticks(yrs)
    pbi.gridlines(ax)
    pbi.dot_legend(ax, [("2020 Census map (fixed)", pbi.BLUE), ("FARS rural/urban label", pbi.ORANGE)])
    finish(fig, "fig2_rural_share_two_definitions", a.final)

    # Figure 3: county map, road deaths per 100,000 residents, 2020-2024 (Power BI filled map look)
    cty = gpd.read_file(os.path.join(ROOT, "data", "raw", "census", "tl_2020_us_county.zip"))
    cty = cty[~cty.STATEFP.isin(["02", "15", "60", "66", "69", "72", "78"])].to_crs(5070)
    cty["geometry"] = cty.geometry.simplify(500)  # 500 m: invisible at print size, keeps files small
    r = w[w.year >= 2020].groupby("fips").agg(d=("deaths", "sum"), p=("population", "sum")).reset_index()
    r["rate"] = r.d / r.p * 1e5
    m = cty.merge(r, left_on="GEOID", right_on="fips", how="left")
    bins = [0, 5, 10, 15, 20, 30, 40, np.inf]
    labels = ["<5", "5-10", "10-15", "15-20", "20-30", "30-40", "40+"]
    m["cls"] = pd.cut(m.rate, bins, labels=labels, right=False)
    fig, ax = plt.subplots(figsize=(10, 6.6))
    fig.subplots_adjust(top=0.76, bottom=0.07, left=0.01, right=0.99)
    pbi.title(fig, "Road death rate by county, 2020-2024", "Deaths per 100,000 residents per year, lower 48 states")
    for lab, col in zip(labels, pbi.SEQ):
        m[m.cls == lab].plot(ax=ax, color=col, edgecolor="white", linewidth=0.12)
    cty.dissolve("STATEFP").boundary.plot(ax=ax, color="white", linewidth=0.7)
    ax.set_axis_off()
    # horizontal stepped legend under the title, Power BI style
    lx = fig.add_axes([0.02, 0.83, 0.42, 0.022])
    for i, c in enumerate(pbi.SEQ):
        lx.add_patch(plt.Rectangle((i, 0), 0.96, 1, color=c))
        lx.text(i + 0.48, -0.6, labels[i], ha="center", va="top", fontsize=8, color=pbi.LABEL)
    lx.set_xlim(0, len(pbi.SEQ))
    lx.set_ylim(0, 1)
    lx.set_axis_off()
    finish(fig, "fig3_county_death_rate_map", a.final, SRC + " Alaska and Hawaii appear in the online atlas.", exts=("png", "pdf"))

    # Figure 4: rural deaths by person type (Power BI small-multiples column chart)
    pt = w.groupby("year")[["deaths_rural_driver", "deaths_rural_passenger", "deaths_rural_pedestrian", "deaths_rural_cyclist"]].sum()
    fig, axes = plt.subplots(1, 4, figsize=(11, 4.2))
    fig.subplots_adjust(top=0.68, bottom=0.17, left=0.05, right=0.99, wspace=0.28)
    pbi.title(fig, "Rural road deaths by person type, 2015-2024", "Each panel has its own scale; 2024 bar highlighted")
    for ax, (col, lab) in zip(axes, [("deaths_rural_driver", "Drivers"), ("deaths_rural_passenger", "Passengers"),
                                     ("deaths_rural_pedestrian", "Pedestrians"), ("deaths_rural_cyclist", "Cyclists")]):
        colors = [pbi.SEQ[2]] * (len(yrs) - 1) + [pbi.BLUE]
        ax.bar(yrs, pt[col], color=colors, width=0.72)
        ax.set_ylim(0, pt[col].max() * 1.25)
        ax.set_title(lab, loc="left", fontsize=10.5, color=pbi.TITLE, fontweight="bold", pad=20)
        ax.set_xticks([2015, 2020, 2024])
        pbi.thousands(ax)
        chg = (pt[col].iloc[-1] / pt[col].iloc[0] - 1) * 100
        ax.annotate(f"{pt[col].iloc[-1]:,}", (yrs[-1], pt[col].iloc[-1]), xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5, color=pbi.TITLE, fontweight="bold")
        ax.text(0.0, 1.05, f"2024 vs 2015: {chg:+.0f}%", transform=ax.transAxes, fontsize=8.5, color=pbi.LABEL, va="bottom")
        pbi.gridlines(ax)
    finish(fig, "fig4_rural_deaths_by_person_type", a.final)
    print("figures written to", F)


if __name__ == "__main__":
    main()
