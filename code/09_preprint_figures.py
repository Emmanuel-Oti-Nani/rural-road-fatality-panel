#!/usr/bin/env python3
"""
09_preprint_figures.py - Figures for the validation preprint, sized for a two-column page.

PLAIN-LANGUAGE NOTE: Draws the three figures in the preprint from the validation
tables (no numbers typed by hand). Output: paper/preprint/fig*.pdf and .png.
"""
import json
import os

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "paper", "validation_tables")
O = os.path.join(ROOT, "paper", "preprint")
os.makedirs(O, exist_ok=True)
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
import pbi_style as pbi  # Power BI visual style shared with the release figures

pbi.apply(7.5)
plt.rcParams.update({"savefig.dpi": 300, "lines.linewidth": 1.8})
BLUE, ORANGE, INK, INK2, GRID = pbi.BLUE, pbi.ORANGE, pbi.TITLE, pbi.LABEL, pbi.GRID
W = 3.4  # one REVTeX column, inches


def save(fig, name):
    fig.savefig(os.path.join(O, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(O, name + ".png"), bbox_inches="tight")
    plt.close(fig)


def grid(ax):
    pbi.gridlines(ax)


# FIG. 1: rural share by year under both definitions (compared deaths)
by = pd.read_csv(os.path.join(T, "agreement_by_year.csv"))
fig, ax = plt.subplots(figsize=(W, 2.3))
for col, c in [("pct_rural_census", BLUE), ("pct_rural_fars", ORANGE)]:
    ax.plot(by.year, by[col], color=c)
    ax.plot(by.year.iloc[-1], by[col].iloc[-1], "o", color=c, ms=4.5, mec="white", mew=1)
    ax.annotate(f"{by[col].iloc[-1]:.1f}%", (by.year.iloc[-1], by[col].iloc[-1]), xytext=(4, 0), textcoords="offset points",
                va="center", fontsize=7.5, fontweight="bold", color=INK)
ax.fill_between(by.year, by.pct_rural_fars, by.pct_rural_census, color=BLUE, alpha=0.06, lw=0)
ax.set_xticks(by.year)
ax.set_xticklabels([str(y) if y in (2015, 2018, 2021, 2024) else "" for y in by.year])
ax.set_ylim(35, 55)
ax.set_yticks([35, 40, 45, 50, 55])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_ylabel("Rural share of deaths")
ax.set_xlim(2014.6, 2025.0)
pbi.dot_legend(ax, [("2020 Census map", BLUE), ("FARS label", ORANGE)])
grid(ax)
save(fig, "fig1_rural_share")

# FIG. 2: distance from Census-rural crashes to the nearest 2020 urban area, by FARS label
x = pd.read_csv(os.path.join(ROOT, "data", "processed", "crash_crosswalk_2015_2024.csv"), dtype={"fips": str},
                usecols=["fatals", "ru_census", "ru_fars", "latitude", "longitude"])
cr = x[(x.ru_census == "rural") & x.ru_fars.isin(["rural", "urban"])]
ua = gpd.read_file(os.path.join(ROOT, "data", "raw", "census", "tl_2023_us_uac20.zip"), columns=["UACE20"]).to_crs(5070)
pts = gpd.GeoDataFrame(cr[["fatals", "ru_fars"]], geometry=gpd.points_from_xy(cr.longitude, cr.latitude), crs=4326).to_crs(5070)
near = gpd.sjoin_nearest(pts, ua[["geometry"]], how="left", distance_col="d")
near = near[~near.index.duplicated()]
near["km"] = (near.d / 1000).clip(lower=0.01)
fig, ax = plt.subplots(figsize=(W, 2.3))
for lab, c, name in [("urban", ORANGE, "FARS label urban"), ("rural", BLUE, "FARS label rural")]:
    g = near[near.ru_fars == lab].sort_values("km")
    cum = g.fatals.cumsum() / g.fatals.sum()
    ax.step(g.km, cum * 100, where="post", color=c)
ax.set_xscale("log")
ax.set_xlim(0.05, 100)
ax.set_xticks([0.1, 1, 10, 100])
ax.set_xticklabels(["0.1", "1", "10", "100"])
ax.tick_params(which="minor", length=0)
ax.axvline(1, color=INK2, lw=0.6, ls=":")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_ylabel("Cumulative share of deaths")
ax.set_xlabel("Distance to nearest 2020 Census urban area (km)")
med = {lab: near[near.ru_fars == lab].km.median() for lab in ("urban", "rural")}
pbi.dot_legend(ax, [(f"FARS urban (median {med['urban']:.2f} km)", ORANGE), (f"FARS rural (median {med['rural']:.2f} km)", BLUE)])
grid(ax)
save(fig, "fig2_distance_ecdf")

# FIG. 3: FARS rural share by year, four states with the largest divergence, with the Census-map share
yr = pd.read_csv(os.path.join(T, "fars_rural_share_by_state_year.csv"), index_col=0)
xs = x  # reuse
cw = pd.read_csv(os.path.join(ROOT, "data", "processed", "crash_crosswalk_2015_2024.csv"), dtype={"fips": str},
                 usecols=["year", "fatals", "fips", "ru_census", "ru_fars"])
cw = cw[cw.ru_census.isin(["rural", "urban"]) & cw.ru_fars.isin(["rural", "urban"])]
st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).set_index("fips_state")
cw["state"] = cw.fips.str[:2].map(st.abbr)
dv = pd.read_csv(os.path.join(T, "state_divergence_2015_16_vs_2023_24.csv"))
top = list(dv[dv.deaths_2015_16_and_2023_24 >= 2000].sort_values("divergence").state[:4])  # larger states: less year-to-year noise
fig, axes = plt.subplots(2, 2, figsize=(W, 3.0), sharex=True)
for ax, s_ in zip(axes.flat, top):
    g = cw[cw.state == s_]
    cen = g.groupby("year").apply(lambda h: (h.fatals * (h.ru_census == "rural")).sum() / h.fatals.sum() * 100, include_groups=False)
    ax.plot(yr.columns.astype(int), yr.loc[s_].values, color=ORANGE, lw=1.5)
    ax.plot(cen.index, cen.values, color=BLUE, lw=1.5)
    lo = min(yr.loc[s_].min(), cen.min())
    hi = max(yr.loc[s_].max(), cen.max())
    ax.set_ylim(max(0, lo - 8), min(100, hi + 8))
    ax.set_title(st.set_index("abbr").state_name[s_], fontsize=8.5, loc="left", fontweight="bold", color=INK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xticks([2015, 2018, 2021, 2024])
    grid(ax)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([], [], marker="o", ls="", ms=6, color=BLUE, label="Census map"),
                    Line2D([], [], marker="o", ls="", ms=6, color=ORANGE, label="FARS label")],
           loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.04), handletextpad=0.3)
fig.supylabel("Rural share of deaths", fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "fig3_state_series")
print("preprint figures written:", O, top)
