#!/usr/bin/env python3
"""
04_validation.py - Validation study: how well does the FARS rural/urban label agree
with the 2020 Census urban-area map?

PLAIN-LANGUAGE NOTE: Police and FARS analysts record whether each fatal crash was
rural or urban (variable RUR_URB). This script checks that label against where the
crash's map point actually falls on the 2020 Census urban-area map, crash by crash.
It reports how often they agree, in which direction they disagree, and how this
changes by year, state, and road type. Results go to paper/validation_tables/ and
paper/stats.json. A random sample of disagreements is written for you to inspect
by hand (paper/validation_tables/disagreement_sample.csv).

Reference standard: the 2020 Census urban areas (criteria published Dec 2022),
applied to every year. Comparison: FARS RUR_URB (1 = rural, 2 = urban), which
follows FHWA adjusted urban boundaries in force when the crash was coded.
Crashes with no usable map point or an unknown FARS label are excluded.
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
T = os.path.join(ROOT, "paper", "validation_tables")
os.makedirs(T, exist_ok=True)


def agree(df, w="fatals"):
    """Agreement statistics, weighted by deaths (w='fatals') or by crashes (w=None)."""
    wt = df[w] if w else pd.Series(1, index=df.index)
    a = wt[(df.ru_fars == "rural") & (df.ru_census == "rural")].sum()   # both rural
    b = wt[(df.ru_fars == "urban") & (df.ru_census == "rural")].sum()   # Census rural, FARS urban
    c = wt[(df.ru_fars == "rural") & (df.ru_census == "urban")].sum()   # Census urban, FARS rural
    d = wt[(df.ru_fars == "urban") & (df.ru_census == "urban")].sum()   # both urban
    n = a + b + c + d
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / n ** 2
    return {"n": int(n), "both_rural": int(a), "census_rural_fars_urban": int(b),
            "census_urban_fars_rural": int(c), "both_urban": int(d),
            "pct_agree": round(po * 100, 2), "kappa": round((po - pe) / (1 - pe), 3) if pe < 1 else None,
            "sensitivity_fars_rural": round(a / (a + b) * 100, 2) if a + b else None,
            "specificity_fars_rural": round(d / (c + d) * 100, 2) if c + d else None,
            "pct_rural_census": round((a + b) / n * 100, 2), "pct_rural_fars": round((a + c) / n * 100, 2)}


def main():
    x = pd.read_csv(os.path.join(P, "crash_crosswalk_2015_2024.csv"), dtype={"fips": str, "st_case": str},
                    usecols=["year", "st_case", "fatals", "fips", "ru_census", "ru_fars", "road_class",
                             "latitude", "longitude", "ua_name20", "place_namelsad"])
    n0 = len(x)
    v = x[x.ru_census.isin(["rural", "urban"]) & x.ru_fars.isin(["rural", "urban"])].copy()
    v["state"] = v.fips.str[:2]
    st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).set_index("fips_state").abbr
    v["state"] = v.state.map(st)
    stats = {"crashes_all": int(n0), "crashes_compared": int(len(v)),
             "crashes_excluded": int(n0 - len(v)), "deaths_compared": int(v.fatals.sum())}

    overall = agree(v)
    stats["overall_deaths"] = overall
    stats["overall_crashes"] = agree(v, None)
    by_year = pd.DataFrame({y: agree(g) for y, g in v.groupby("year")}).T
    by_year.index.name = "year"
    by_year.to_csv(os.path.join(T, "agreement_by_year.csv"))
    by_state = pd.DataFrame({s: agree(g) for s, g in v[v.year >= 2022].groupby("state")}).T
    by_state.index.name = "state"
    by_state.sort_values("pct_agree").to_csv(os.path.join(T, "agreement_by_state_2022_2024.csv"))
    by_road = pd.DataFrame({r: agree(g) for r, g in v.groupby("road_class")}).T
    by_road.index.name = "road_class"
    by_road.to_csv(os.path.join(T, "agreement_by_road_class.csv"))
    # early vs late period
    stats["period_2015_2019"] = agree(v[v.year <= 2019])
    stats["period_2020_2024"] = agree(v[v.year >= 2020])
    stats["by_year"] = {int(k): {kk: (None if vv is None or (isinstance(vv, float) and np.isnan(vv)) else float(vv) if isinstance(vv, (float, np.floating)) else int(vv)) for kk, vv in r.items()}
                        for k, r in by_year.iterrows()}
    stats["states_lowest_agreement_2022_2024"] = json.loads(by_state.sort_values("pct_agree").head(5)[["pct_agree", "kappa", "n"]].reset_index().to_json(orient="records"))
    stats["states_highest_agreement_2022_2024"] = json.loads(by_state.sort_values("pct_agree").tail(5)[["pct_agree", "kappa", "n"]].reset_index().to_json(orient="records"))

    # State divergence over time: change in rural share 2015-2016 vs 2023-2024 under each definition
    def share(g, col):
        return float((g.fatals * (g[col] == "rural")).sum() / g.fatals.sum() * 100)
    rows = []
    for s_, g in v.groupby("state"):
        a, b = g[g.year.between(2015, 2016)], g[g.year.between(2023, 2024)]
        rows.append({"state": s_, "deaths_2015_16_and_2023_24": int(a.fatals.sum() + b.fatals.sum()),
                     "fars_2015_16": share(a, "ru_fars"), "fars_2023_24": share(b, "ru_fars"),
                     "census_2015_16": share(a, "ru_census"), "census_2023_24": share(b, "ru_census")})
    dv = pd.DataFrame(rows)
    dv["change_fars"] = dv.fars_2023_24 - dv.fars_2015_16
    dv["change_census"] = dv.census_2023_24 - dv.census_2015_16
    dv["divergence"] = dv.change_fars - dv.change_census
    dv = dv.sort_values("divergence").round(1)
    dv.to_csv(os.path.join(T, "state_divergence_2015_16_vs_2023_24.csv"), index=False)
    stats["state_divergence_top"] = json.loads(dv.head(6).to_json(orient="records"))
    stats["states_divergence_below_minus5"] = int((dv.divergence <= -5).sum())
    stats["states_divergence_above_plus5"] = int((dv.divergence >= 5).sum())
    yr = v.groupby(["state", "year"]).apply(lambda g: share(g, "ru_fars"), include_groups=False).unstack().round(1)
    yr.to_csv(os.path.join(T, "fars_rural_share_by_state_year.csv"))
    stats["fars_rural_share_state_year"] = {s_: {str(k): float(val) for k, val in yr.loc[s_].items()} for s_ in dv.head(4).state}

    # Distance from crashes outside Census urban areas to the nearest 2020 urban area, by FARS label
    import geopandas as gpd
    ua = gpd.read_file(os.path.join(ROOT, "data", "raw", "census", "tl_2023_us_uac20.zip"), columns=["UACE20"]).to_crs(5070)
    cr = v[v.ru_census == "rural"]
    pts = gpd.GeoDataFrame(cr[["fatals", "ru_fars", "year"]], geometry=gpd.points_from_xy(cr.longitude, cr.latitude), crs=4326).to_crs(5070)
    near = gpd.sjoin_nearest(pts, ua[["geometry"]], how="left", distance_col="dist_m")
    near = near[~near.index.duplicated()]
    dist = {}
    for lab, g in near.groupby("ru_fars"):
        w = g.fatals
        dist[lab] = {"deaths": int(w.sum()),
                     "median_km": round(float(g.dist_m.median() / 1000), 2),
                     "pct_within_1km": round(float(w[g.dist_m <= 1000].sum() / w.sum() * 100), 1),
                     "pct_within_2km": round(float(w[g.dist_m <= 2000].sum() / w.sum() * 100), 1),
                     "pct_within_5km": round(float(w[g.dist_m <= 5000].sum() / w.sum() * 100), 1)}
    stats["census_rural_distance_to_urban_area"] = dist
    pd.DataFrame(dist).T.to_csv(os.path.join(T, "census_rural_distance_to_urban_area.csv"))

    # Hand-check sample: 40 disagreements (2024), fixed random seed so it is reproducible
    dis = v[(v.year == 2024) & (v.ru_fars != v.ru_census)]
    samp = dis.sample(n=min(40, len(dis)), random_state=20261021).copy()
    samp["google_maps_link"] = "https://www.google.com/maps?q=" + samp.latitude.astype(str) + "," + samp.longitude.astype(str)
    samp["your_judgment"] = ""
    samp.to_csv(os.path.join(T, "disagreement_sample.csv"), index=False)

    sp = os.path.join(ROOT, "paper", "stats.json")
    s = json.load(open(sp)) if os.path.exists(sp) else {}
    s["validation"] = stats
    json.dump(s, open(sp, "w"), indent=2, default=float)
    print(json.dumps(overall, indent=2))
    print(by_year[["n", "pct_agree", "kappa", "sensitivity_fars_rural", "specificity_fars_rural", "pct_rural_census", "pct_rural_fars"]].to_string())
    print(by_road[["n", "pct_agree", "kappa"]].to_string())
    print(by_state.sort_values("pct_agree")[["n", "pct_agree", "kappa"]].head(8).to_string())


if __name__ == "__main__":
    main()
