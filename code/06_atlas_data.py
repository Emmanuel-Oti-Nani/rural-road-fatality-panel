#!/usr/bin/env python3
"""
06_atlas_data.py - Write the data files the Rural Road Safety Atlas web map reads.

PLAIN-LANGUAGE NOTE: The atlas (atlas/index.html) is a web page that draws a U.S.
county map. This script makes the two small map files it needs: county shapes
with their numbers, and one dot per Census town/city with its 2015-2024 deaths.
It also copies the figures and the panel CSV into the atlas folder so visitors can
download them. You do not need to open this file.
"""
import json
import os
import shutil

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
A = os.path.join(ROOT, "atlas")
os.makedirs(os.path.join(A, "data"), exist_ok=True)
os.makedirs(os.path.join(A, "figures"), exist_ok=True)


def main():
    w = pd.read_csv(os.path.join(P, "panel_county_year_2015_2024.csv"), dtype={"fips": str, "state_fips": str})
    yrs = list(range(2015, 2025))
    rows = {}
    for fips, g in w.sort_values("year").groupby("fips"):
        r5 = g[g.year >= 2020]
        d10 = int(g.deaths.sum())
        known = d10 - int(g.deaths_ru_unknown.sum())
        first = g.iloc[0]
        rows[fips] = {
            "n": f"{first.county_name}, {first.state}",
            "d": [int(v) for v in g.deaths], "r": [int(v) for v in g.deaths_rural],
            "fr": [int(v) for v in g.deaths_fars_rural],
            "rate": round(float(r5.deaths.sum() / r5.population.sum() * 1e5), 1),
            "rs": round(float(g.deaths_rural.sum() / known * 100), 1) if known else None,
            "rsf": round(float(g.deaths_fars_rural.sum() / (d10 - g.deaths_fars_ru_unknown.sum()) * 100), 1)
            if d10 - g.deaths_fars_ru_unknown.sum() else None,
            "pr": float(first.pct_rural_2020) if pd.notna(first.pct_rural_2020) else None,
            "ped": int(g.deaths_pedestrian.sum()), "cyc": int(g.deaths_cyclist.sum()),
            "drv": int(g.deaths_driver.sum()), "pas": int(g.deaths_passenger.sum()),
            "pop": int(g[g.year == 2024].population.iloc[0]),
            "mi": round(float(first.get("miles_total_2024", 0) or 0)),
            "mq": first.get("miles_quality_state", None) if isinstance(first.get("miles_quality_state", None), str) else None,
        }
        rows[fips]["dpm"] = round(sum(rows[fips]["d"][5:]) / 5 / rows[fips]["mi"] * 100, 2) if rows[fips]["mi"] else None

    cty = gpd.read_file(os.path.join(ROOT, "data", "raw", "census", "tl_2020_us_county.zip"))
    cty = cty[cty.GEOID.isin(rows.keys())][["GEOID", "geometry"]].to_crs(4326)
    cty["geometry"] = cty.geometry.simplify(0.01, preserve_topology=True)
    feats = []
    for _, c in cty.iterrows():
        feats.append({"type": "Feature", "id": c.GEOID, "properties": {"f": c.GEOID, **rows[c.GEOID]},
                      "geometry": json.loads(gpd.GeoSeries([c.geometry]).to_json())["features"][0]["geometry"]})
    gj = {"type": "FeatureCollection", "years": yrs, "features": feats}
    s = json.dumps(gj, separators=(",", ":"))
    # round coordinates to 3 decimals (about 100 m) to keep the file small
    import re
    s = re.sub(r"(-?\d+\.\d{3})\d+", r"\1", s)
    open(os.path.join(A, "data", "counties.geojson"), "w").write(s)

    # Place view: deaths 2015-2024 by 2020 Census place (incorporated places and CDPs)
    x = pd.read_csv(os.path.join(P, "crash_crosswalk_2015_2024.csv"), dtype={"place_geoid": str},
                    usecols=["year", "fatals", "place_geoid", "place_namelsad", "place_funcstat", "ru_census"])
    x = x[x.place_geoid.notna()]
    pl = x.groupby(["place_geoid", "place_namelsad", "place_funcstat"]).agg(
        d=("fatals", "sum"), d5=("fatals", lambda s: int(s[x.loc[s.index, "year"] >= 2020].sum()))).reset_index()
    import glob
    cents = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "raw", "census", "place", "*.zip"))):
        g = gpd.read_file(f, columns=["GEOID", "INTPTLAT", "INTPTLON"], ignore_geometry=True)
        cents.append(g)
    cents = pd.concat(cents)
    pl = pl.merge(cents, left_on="place_geoid", right_on="GEOID")
    st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).set_index("fips_state").abbr
    pts = [{"n": f"{r.place_namelsad}, {st.get(r.place_geoid[:2], '')}", "g": r.place_geoid, "c": r.place_funcstat == "S",
            "d": int(r.d), "d5": int(r.d5), "lat": round(float(r.INTPTLAT), 4), "lon": round(float(r.INTPTLON), 4)}
           for r in pl.itertuples()]
    json.dump(pts, open(os.path.join(A, "data", "places.json"), "w"), separators=(",", ":"))

    for f in os.listdir(os.path.join(ROOT, "paper", "figures")):
        shutil.copy(os.path.join(ROOT, "paper", "figures", f), os.path.join(A, "figures", f))
    shutil.copy(os.path.join(P, "panel_county_year_2015_2024.csv"), os.path.join(A, "data", "panel_county_year_2015_2024.csv"))
    print("counties", len(feats), "places", len(pts),
          "geojson MB", round(len(s) / 1e6, 2))


if __name__ == "__main__":
    main()
