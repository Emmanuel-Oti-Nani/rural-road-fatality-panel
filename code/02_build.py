#!/usr/bin/env python3
"""
02_build.py - Turn the raw FARS crash and person files into the county-by-year panel.

PLAIN-LANGUAGE NOTE: This is the heart of the project. For every fatal crash
from 2015 to 2024 it (1) decides which county the crash belongs to, (2) checks
the crash's map point against the 2020 Census urban-area map to label it rural
or urban, (3) finds the Census town/city and county subdivision it fell in, and
(4) counts deaths by who died and by type and owner of road. It then adds
population and road miles and writes the panel files. You do not need to open
this file; the rules it follows are listed in docs/JOIN_RULES.md in plain words.

Outputs (data/processed/):
  crash_crosswalk_2015_2024.csv   one row per fatal crash, with county, place,
                                  county subdivision, rural/urban, and match flags
  panel_county_year_2015_2024.csv one row per county per year (wide)
  panel_county_year_long.csv      deaths by county, year, rural/urban, road class,
                                  road owner, and person type (long)
  build_log.json                  row counts at every step (read by 03_qa.py)
"""
import glob
import json
import os
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(OUT, exist_ok=True)
YEARS = list(range(2015, 2025))
STATES = {"01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18",
          "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
          "34", "35", "36", "37", "38", "39", "40", "41", "42", "44", "45", "46", "47", "48", "49",
          "50", "51", "53", "54", "55", "56"}
LOG = {}

# ---------------------------------------------------------------- code groupings
# FARS PER_TYP (person type). Deaths are persons with INJ_SEV == 4 (fatal injury).
PERSON = {1: "driver", 2: "passenger", 3: "occupant_other", 9: "occupant_other",
          5: "pedestrian", 6: "cyclist", 7: "cyclist",
          4: "nonmotorist_other", 8: "nonmotorist_other", 10: "nonmotorist_other",
          19: "nonmotorist_other"}
# FARS FUNC_SYS (functional system of the road where the crash happened)
ROAD = {1: "interstate_fwy", 2: "interstate_fwy", 3: "arterial", 4: "arterial",
        5: "collector", 6: "collector", 7: "local"}  # 96, 97, 98, 99 -> road_unknown


def owner_group(c):
    """FARS RD_OWNER and HPMS OWNERSHIP share one code list."""
    if pd.isna(c):
        return "owner_unknown"
    c = int(c)
    if c in (1, 11, 21, 31):
        return "state"
    if c == 2:
        return "county"
    if c in (3, 4, 12, 25, 32):
        return "town_city"
    if c in (50, 62) or 60 <= c <= 80:
        return "federal_tribal"
    if c in (26, 27, 40):
        return "other_public_private"
    return "owner_unknown"


# FARS county codes that are not 2020 counties but have a one-to-one successor
RECODE = {"46113": "46102",  # Shannon County SD renamed Oglala Lakota County (2015)
          "02270": "02158"}  # Wade Hampton Census Area AK renamed Kusilvak (2015)
# Codes that split: resolved from the crash's map point (02261 Valdez-Cordova -> 02063 / 02066)


def read_fars(y, name, cols):
    z = zipfile.ZipFile(os.path.join(RAW, "fars", f"FARS{y}NationalCSV.zip"))
    member = [f for f in z.namelist() if f.lower().endswith("/" + name) or f.lower() == name][0]
    d = pd.read_csv(z.open(member), encoding="latin-1", low_memory=False)
    d.columns = [c.replace("﻿", "").replace("ï»¿", "").strip().upper() for c in d.columns]
    return d[cols].copy()


def load_geo():
    cty = gpd.read_file(os.path.join(RAW, "census", "tl_2020_us_county.zip"))
    cty = cty[cty.STATEFP.isin(STATES)][["GEOID", "NAME", "NAMELSAD", "STATEFP", "ALAND", "geometry"]]
    ua = gpd.read_file(os.path.join(RAW, "census", "tl_2023_us_uac20.zip"))[["UACE20", "NAME20", "geometry"]]
    places, cousubs = [], []
    for f in sorted(glob.glob(os.path.join(RAW, "census", "place", "*.zip"))):
        p = gpd.read_file(f)[["GEOID", "NAMELSAD", "FUNCSTAT", "CLASSFP", "geometry"]]
        places.append(p)
    for f in sorted(glob.glob(os.path.join(RAW, "census", "cousub", "*.zip"))):
        c = gpd.read_file(f)[["GEOID", "NAMELSAD", "FUNCSTAT", "geometry"]]
        cousubs.append(c)
    pl = gpd.GeoDataFrame(pd.concat(places, ignore_index=True), crs=places[0].crs)
    cs = gpd.GeoDataFrame(pd.concat(cousubs, ignore_index=True), crs=cousubs[0].crs)
    return cty, ua.to_crs(cty.crs), pl.to_crs(cty.crs), cs.to_crs(cty.crs)


def point_join(pts, poly, cols, prefix):
    j = gpd.sjoin(pts[["geometry"]], poly[cols + ["geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]  # a point on a shared border: keep the first match
    return j[cols].rename(columns={c: prefix + c for c in cols})


def build_crashes(cty, ua, pl, cs):
    acc_cols = ["STATE", "ST_CASE", "COUNTY", "FATALS", "LATITUDE", "LONGITUD", "RUR_URB",
                "FUNC_SYS", "RD_OWNER", "ROUTE"]
    frames = []
    for y in YEARS:
        a = read_fars(y, "accident.csv", acc_cols)
        a["YEAR"] = y
        frames.append(a)
    a = pd.concat(frames, ignore_index=True)
    LOG["fars_crashes_read"] = int(len(a))
    LOG["fars_fatals_by_year"] = {int(k): int(v) for k, v in a.groupby("YEAR").FATALS.sum().items()}

    # --- valid coordinates (FARS uses 77.7777 / 88.8888 / 99.9999 as missing codes)
    a["coord_valid"] = (a.LATITUDE.between(17, 72) & a.LONGITUD.between(-180, -64))
    LOG["crashes_without_valid_coords"] = int((~a.coord_valid).sum())
    pts = gpd.GeoDataFrame(a, geometry=gpd.points_from_xy(a.LONGITUD, a.LATITUDE), crs="EPSG:4326").to_crs(cty.crs)
    v = pts[pts.coord_valid]

    j_cty = point_join(v, cty, ["GEOID"], "pt_county_")
    j_ua = point_join(v, ua, ["UACE20", "NAME20"], "ua_")
    j_pl = point_join(v, pl, ["GEOID", "NAMELSAD", "FUNCSTAT"], "place_")
    j_cs = point_join(v, cs, ["GEOID", "NAMELSAD", "FUNCSTAT"], "cousub_")
    a = a.join(j_cty).join(j_ua).join(j_pl).join(j_cs)
    a.loc[a.coord_valid & a.pt_county_GEOID.isna(), "coord_valid"] = False  # point fell outside the U.S. map
    LOG["crashes_point_outside_us"] = int((a.LATITUDE.between(17, 72) & a.LONGITUD.between(-180, -64)).sum() - a.coord_valid.sum())

    # --- county assignment (join rules in docs/JOIN_RULES.md)
    valid = set(cty.GEOID)
    a["fars_county_code"] = a.STATE.astype(int).map("{:02d}".format) + a.COUNTY.astype(int).map("{:03d}".format)
    coded = a.fars_county_code.replace(RECODE)
    a["county_rule"] = np.select(
        [coded.isin(valid) & a.fars_county_code.isin(RECODE.keys()),
         coded.isin(valid),
         a.coord_valid],
        ["R2_recoded_successor", "R1_fars_code", "R3_map_point"], default="R4_unassigned")
    a["fips"] = np.where(a.county_rule.isin(["R1_fars_code", "R2_recoded_successor"]), coded,
                         np.where(a.county_rule == "R3_map_point", a.pt_county_GEOID, None))
    a["county_point_agrees"] = np.where(a.coord_valid, a.fips == a.pt_county_GEOID, np.nan)
    LOG["county_rule_counts"] = a.county_rule.value_counts().to_dict()

    # --- rural / urban
    a["ru_census"] = np.where(~a.coord_valid, "unknown", np.where(a.ua_UACE20.notna(), "urban", "rural"))
    a["ru_fars"] = a.RUR_URB.map({1: "rural", 2: "urban"}).fillna("unknown")
    a["road_class"] = a.FUNC_SYS.map(ROAD).fillna("road_unknown")
    a["road_owner"] = a.RD_OWNER.map(owner_group)

    # --- place / county subdivision match flags
    a["place_match"] = np.where(~a.coord_valid, "no_coords",
                                np.where(a.place_GEOID.isna(), "outside_any_place",
                                         np.where(a.place_FUNCSTAT == "S", "in_cdp", "in_incorporated_place")))
    a["cousub_match"] = np.where(~a.coord_valid, "no_coords",
                                 np.where(a.cousub_GEOID.isna(), "no_match",
                                          np.where(a.cousub_GEOID.str.endswith("00000"), "subdivision_not_defined", "matched")))
    return a


def build_persons(crashes):
    frames = []
    for y in YEARS:
        p = read_fars(y, "person.csv", ["ST_CASE", "PER_TYP", "INJ_SEV"])
        p["YEAR"] = y
        frames.append(p[p.INJ_SEV == 4])
    p = pd.concat(frames, ignore_index=True)
    p["person_type"] = p.PER_TYP.map(PERSON).fillna("nonmotorist_other")
    LOG["deaths_person_file_by_year"] = {int(k): int(v) for k, v in p.groupby("YEAR").size().items()}
    keep = ["YEAR", "ST_CASE", "fips", "ru_census", "ru_fars", "road_class", "road_owner"]
    p = p.merge(crashes[keep], on=["YEAR", "ST_CASE"], how="left", validate="many_to_one")
    LOG["deaths_without_crash_record"] = int(p.ru_census.isna().sum())
    return p


def population(cty):
    """Census Population Estimates (July 1). Vintage 2019 for 2015-2019, Vintage 2024 for 2020-2024."""
    v19 = pd.read_csv(os.path.join(RAW, "census", "co-est2019-alldata.csv"), encoding="latin-1", dtype={"STATE": str, "COUNTY": str})
    v24 = pd.read_csv(os.path.join(RAW, "census", "co-est2024-alldata.csv"), encoding="latin-1", dtype={"STATE": str, "COUNTY": str})
    rows = []
    for df, yrs, vint in [(v19, range(2015, 2020), "V2019"), (v24, range(2020, 2025), "V2024")]:
        df = df[(df.SUMLEV == 50)]
        for y in yrs:
            rows.append(pd.DataFrame({"fips": df.STATE + df.COUNTY, "year": y,
                                      "population": df[f"POPESTIMATE{y}"], "pop_source": f"PEP {vint}"}))
    pop = pd.concat(rows, ignore_index=True)

    # Connecticut 2020-2024: Census now publishes planning regions. Rebuild the 8 legacy
    # counties (the geography FARS still codes) by summing town estimates.
    towns = pd.read_csv(os.path.join(RAW, "census", "sub-est2024_9.csv"), encoding="latin-1", dtype=str)
    towns = towns[towns.SUMLEV == "061"]
    cs = gpd.read_file(os.path.join(RAW, "census", "cousub", "tl_2020_09_cousub.zip"))[["COUSUBFP", "COUNTYFP"]]
    towns = towns.merge(cs, left_on="COUSUB", right_on="COUSUBFP", how="left")
    LOG["ct_towns_unmatched"] = int(towns.COUNTYFP.isna().sum())
    ct = []
    for y in range(2020, 2025):
        g = towns.groupby("COUNTYFP")[f"POPESTIMATE{y}"].apply(lambda s: s.astype(int).sum())
        ct.append(pd.DataFrame({"fips": "09" + g.index, "year": y, "population": g.values,
                                "pop_source": "PEP V2024 CT towns summed to legacy county"}))
    pop = pd.concat([pop[~((pop.fips.str[:2] == "09") & (pop.year >= 2020))]] + ct, ignore_index=True)

    # Alaska 2015-2019: Valdez-Cordova (02261) split in 2019 into Chugach (02063) and
    # Copper River (02066). Split its 2015-2019 estimate by 2020 Census population shares.
    ua_cty = pd.read_excel(os.path.join(RAW, "census", "2020_UA_COUNTY.xlsx"), dtype={"STATE": str, "COUNTY": str})
    c20 = ua_cty.assign(fips=ua_cty.STATE + ua_cty.COUNTY).set_index("fips").POP_COU.astype(float)
    share63 = c20["02063"] / (c20["02063"] + c20["02066"])
    vc = pop[(pop.fips == "02261")]
    add = []
    for fips, sh in [("02063", share63), ("02066", 1 - share63)]:
        t = vc.copy()
        t["fips"], t["population"] = fips, (t.population * sh).round().astype(int)
        t["pop_source"] = "PEP V2019 Valdez-Cordova split by 2020 Census shares"
        add.append(t)
    pop = pd.concat([pop[pop.fips != "02261"]] + add, ignore_index=True)
    pop = pop[pop.fips.isin(set(cty.GEOID))]
    pop["pop_imputed"] = pop.pop_source.str.contains("split|summed")
    LOG["population_rows"] = int(len(pop))
    return pop, ua_cty


def hpms_miles():
    rows, spatial_states = [], []
    for f in sorted(glob.glob(os.path.join(RAW, "hpms", "hpms_*.json"))):
        d = json.load(open(f))
        sp = d.get("spatial_rows")
        if sp:
            spatial_states.append(d["state"])
        for key in ("all", "rural"):
            for r in d["rows"][key]:
                if r["county_id"] is None and sp:
                    continue  # replaced by the map-overlap pass below
                rows.append({"state": d["state"], "scope": key, "method": "county_code", **r})
            for r in (sp or {}).get(key, []):
                rows.append({"state": d["state"], "scope": key, "method": "map_overlap", **r})
    h = pd.DataFrame(rows)
    if h.empty:
        return None
    LOG["hpms_states_with_map_overlap_pass"] = spatial_states
    st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str)
    h = h.merge(st, left_on="state", right_on="abbr")
    h["fips"] = h.fips_state + h.county_id.fillna(-1).astype(int).map(lambda c: f"{c:03d}" if c >= 0 else "999")
    h["fips"] = h.fips.replace(RECODE)  # HPMS also still uses the old Shannon County, SD code
    h["road_class"] = h.f_system.map(ROAD).fillna("road_unknown")
    h["road_owner"] = h.ownership.map(owner_group)
    LOG["hpms_miles_total_all"] = float(h[h.scope == "all"].miles.sum())
    return h


def hm20():
    """FHWA Highway Statistics 2024 Table HM-20: official public road length by state."""
    import openpyxl
    ws = openpyxl.load_workbook(os.path.join(RAW, "hpms", "hm20_2024.xlsx"), data_only=True)["A"]
    st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).set_index("state_name").fips_state
    out = {}
    for r in ws.iter_rows(values_only=True):
        v = [c for c in r if c is not None]
        if v and isinstance(v[0], str) and v[0] in st.index and len(v) >= 18:
            # columns: rural Int, OFE, OPA, MinArt, MajColl, MinColl, Local, Total, urban (same 8), grand total
            out[st[v[0]]] = {"hm20_total": float(v[17]), "hm20_local": float(v[7]) + float(v[15]),
                             "hm20_rural_total": float(v[8])}
    return pd.DataFrame(out).T


def main():
    cty, ua, pl, cs = load_geo()
    crashes = build_crashes(cty, ua, pl, cs)
    persons = build_persons(crashes)

    # ---------------- crash crosswalk (one row per crash)
    xw = crashes.rename(columns={"YEAR": "year", "ST_CASE": "st_case", "FATALS": "fatals",
                                 "LATITUDE": "latitude", "LONGITUD": "longitude",
                                 "RUR_URB": "fars_rur_urb", "FUNC_SYS": "fars_func_sys",
                                 "RD_OWNER": "fars_rd_owner"})
    xw = xw[["year", "st_case", "fatals", "fars_county_code", "fips", "county_rule", "coord_valid",
             "latitude", "longitude", "pt_county_GEOID", "county_point_agrees", "ru_census", "ua_UACE20",
             "ua_NAME20", "ru_fars", "fars_rur_urb", "fars_func_sys", "road_class", "fars_rd_owner",
             "road_owner", "place_GEOID", "place_NAMELSAD", "place_FUNCSTAT", "place_match",
             "cousub_GEOID", "cousub_NAMELSAD", "cousub_match"]]
    xw.columns = [c.lower() for c in xw.columns]
    xw.to_csv(os.path.join(OUT, "crash_crosswalk_2015_2024.csv"), index=False)
    xw.to_csv(os.path.join(OUT, "crash_crosswalk_2015_2024.csv.gz"), index=False,
              compression={"method": "gzip", "mtime": 0})  # mtime 0 keeps the file byte-identical across runs
    LOG["crosswalk_rows"] = int(len(xw))

    # ---------------- long table (deaths)
    pa = persons[persons.fips.notna()]
    long = (pa.groupby(["fips", "YEAR", "ru_census", "road_class", "road_owner", "person_type"])
            .size().rename("deaths").reset_index().rename(columns={"YEAR": "year", "ru_census": "location"}))
    long.to_csv(os.path.join(OUT, "panel_county_year_long.csv"), index=False)
    LOG["long_rows"] = int(len(long))
    LOG["deaths_unassigned_county"] = int(persons.fips.isna().sum())

    # ---------------- wide panel
    base = pd.MultiIndex.from_product([sorted(cty.GEOID), YEARS], names=["fips", "year"]).to_frame(index=False)
    ca = crashes[crashes.fips.notna()].rename(columns={"YEAR": "year"})
    pa = pa.rename(columns={"YEAR": "year"})
    parts = [
        ca.groupby(["fips", "year"]).size().rename("crashes"),
        ca.groupby(["fips", "year"]).FATALS.sum().rename("deaths"),
        ca.pivot_table(index=["fips", "year"], columns="ru_census", values="ST_CASE", aggfunc="count").add_prefix("crashes_"),
        pa.pivot_table(index=["fips", "year"], columns="ru_census", values="ST_CASE", aggfunc="count").add_prefix("deaths_"),
        pa.pivot_table(index=["fips", "year"], columns="ru_fars", values="ST_CASE", aggfunc="count").add_prefix("deaths_fars_"),
        pa.pivot_table(index=["fips", "year"], columns="person_type", values="ST_CASE", aggfunc="count").add_prefix("deaths_"),
        pa[pa.ru_census == "rural"].pivot_table(index=["fips", "year"], columns="person_type", values="ST_CASE", aggfunc="count").add_prefix("deaths_rural_"),
        pa.pivot_table(index=["fips", "year"], columns="road_class", values="ST_CASE", aggfunc="count").add_prefix("deaths_"),
        pa[pa.ru_census == "rural"].pivot_table(index=["fips", "year"], columns="road_class", values="ST_CASE", aggfunc="count").add_prefix("deaths_rural_"),
        pa.pivot_table(index=["fips", "year"], columns="road_owner", values="ST_CASE", aggfunc="count").add_prefix("deaths_own_"),
        ca.groupby(["fips", "year"]).coord_valid.apply(lambda s: int((~s.astype(bool)).sum())).rename("n_crashes_no_coords"),
        ca[ca.coord_valid.astype(bool)].groupby(["fips", "year"]).county_point_agrees.apply(lambda s: int((s == False).sum())).rename("n_crashes_point_in_other_county"),
    ]
    w = base.set_index(["fips", "year"]).join(parts, how="left").fillna(0)
    w = w.rename(columns={"crashes_unknown": "crashes_ru_unknown", "deaths_unknown": "deaths_ru_unknown",
                          "deaths_fars_unknown": "deaths_fars_ru_unknown"})
    for c in ["crashes_ru_unknown", "deaths_ru_unknown", "deaths_fars_ru_unknown"]:
        if c not in w:
            w[c] = 0
    w = w.astype(int).reset_index()

    pop, ua_cty = population(cty)
    w = w.merge(pop, on=["fips", "year"], how="left")
    u = ua_cty.assign(fips=ua_cty.STATE + ua_cty.COUNTY)[["fips", "POP_COU", "POP_RUR", "POPPCT_RUR"]]
    u.columns = ["fips", "pop2020_census", "pop2020_rural", "pct_rural_2020"]
    u["pct_rural_2020"] = (u.pct_rural_2020.astype(float) * 100).round(2)
    w = w.merge(u, on="fips", how="left")
    w["death_rate_per100k"] = (w.deaths / w.population * 1e5).round(2)

    names = cty[["GEOID", "NAMELSAD", "STATEFP", "ALAND"]].rename(columns={"GEOID": "fips", "NAMELSAD": "county_name", "STATEFP": "state_fips", "ALAND": "land_area_m2"})
    st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).rename(columns={"fips_state": "state_fips"})
    w = w.merge(names, on="fips").merge(st, on="state_fips")

    h = hpms_miles()
    if h is not None:
        m = h.groupby(["fips", "scope"]).miles.sum().unstack().rename(columns={"all": "miles_total_2024", "rural": "miles_rural_fhwa_2024"})
        mc = h[h.scope == "all"].pivot_table(index="fips", columns="road_class", values="miles", aggfunc="sum").add_prefix("miles_").add_suffix("_2024")
        mr = h[h.scope == "rural"].pivot_table(index="fips", columns="road_class", values="miles", aggfunc="sum").add_prefix("miles_rural_").add_suffix("_2024")
        mo = h[h.scope == "all"].pivot_table(index="fips", columns="road_owner", values="miles", aggfunc="sum").add_prefix("miles_own_").add_suffix("_2024")
        miles = pd.concat([m, mc, mr, mo], axis=1).round(2)
        # Mileage quality flag per state: compare map mileage with FHWA's official
        # state totals (Highway Statistics 2024, Table HM-20).
        hm = hm20()
        hs = h[h.scope == "all"].groupby("fips_state").miles.sum()
        hl = h[(h.scope == "all") & (h.road_class == "local")].groupby("fips_state").miles.sum()
        hn = h[(h.scope == "all") & (h.road_class != "local")].groupby("fips_state").miles.sum()
        q = pd.DataFrame({"hpms_map_total": hs, "hpms_map_local": hl, "hpms_map_nonlocal": hn}).join(hm, how="left")
        q["ratio_total"] = (q.hpms_map_total / q.hm20_total).round(3)
        q["ratio_nonlocal"] = (q.hpms_map_nonlocal / (q.hm20_total - q.hm20_local)).round(3)
        q["ratio_local"] = (q.hpms_map_local / q.hm20_local).round(3)
        q["miles_quality"] = np.where(q.ratio_total.between(0.95, 1.05), "complete",
                                      np.where(q.ratio_nonlocal.between(0.95, 1.05), "local_roads_mismatch", "check"))
        q.to_csv(os.path.join(OUT, "hpms_state_check_vs_hm20.csv"))
        LOG["hpms_state_quality"] = q.miles_quality.value_counts().to_dict()
        qf = q.miles_quality.rename("miles_quality_state")
        overlap = h[h.method == "map_overlap"].fips.unique()
        miles["miles_method"] = np.where(miles.index.isin(overlap), "county_code_plus_map_overlap", "county_code")
        miles["miles_quality_state"] = miles.index.str[:2].map(qf)
        unmatched = sorted(set(miles.index) - set(cty.GEOID))
        LOG["hpms_county_codes_not_in_2020_counties"] = unmatched
        LOG["hpms_miles_in_unmatched_codes"] = float(miles.loc[unmatched, "miles_total_2024"].sum()) if unmatched else 0.0
        w = w.merge(miles, left_on="fips", right_index=True, how="left")
        mcols = [c for c in w.columns if c.startswith("miles_") and c not in ("miles_method", "miles_quality_state")]
        w[mcols] = w[mcols].fillna(0)
        w["miles_quality_state"] = w.miles_quality_state.fillna(w.state_fips.map(qf))

    front = ["fips", "state_fips", "abbr", "state_name", "county_name", "year"]
    w = w[front + [c for c in w.columns if c not in front]].rename(columns={"abbr": "state"})
    w.to_csv(os.path.join(OUT, "panel_county_year_2015_2024.csv"), index=False)
    LOG["panel_rows"] = int(len(w))
    LOG["panel_counties"] = int(w.fips.nunique())
    json.dump(LOG, open(os.path.join(OUT, "build_log.json"), "w"), indent=2, default=str)
    print(json.dumps(LOG, indent=2, default=str))


if __name__ == "__main__":
    main()
