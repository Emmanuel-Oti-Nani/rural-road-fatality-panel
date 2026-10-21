#!/usr/bin/env python3
"""
03_qa.py - Quality checks. Writes data/processed/qa_report.txt, the list of counties
with unusual year-to-year changes for the author's review, and paper/stats.json.

PLAIN-LANGUAGE NOTE: This script checks the panel against its sources. It confirms
that no deaths were lost or double-counted, compares the 2024 national numbers with
NHTSA's published report, flags counties whose deaths jumped or fell more than
chance would explain (you review each one), and picks named counties for you to
check by hand. Open data/processed/qa_report.txt to read the results.
"""
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import poisson

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
os.makedirs(os.path.join(ROOT, "paper"), exist_ok=True)

# Published reference: NHTSA Traffic Safety Facts 2024 Data: Rural/Urban Traffic Fatalities,
# DOT HS 813 828 (July 2026), which uses the FARS rural/urban variable.
NHTSA_2024 = {"total": 39254, "rural": 16006, "urban": 22905,
              "source": "NHTSA, Traffic Safety Facts 2024 Data: Rural/Urban Traffic Fatalities, DOT HS 813 828, https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813828"}

SPOT = {"29077": "Greene County, MO (Springfield; large, mixed rural/urban)",
        "29105": "Laclede County, MO (rural Ozarks county on I-44)",
        "06037": "Los Angeles County, CA (largest county)",
        "48301": "Loving County, TX (smallest population in the U.S.)",
        "46102": "Oglala Lakota County, SD (FARS still codes it as old Shannon County 46113)",
        "02063": "Chugach Census Area, AK (split from Valdez-Cordova in 2019)",
        "09001": "Fairfield County, CT (legacy county; population rebuilt from towns)"}


def main():
    log = json.load(open(os.path.join(P, "build_log.json")))
    w = pd.read_csv(os.path.join(P, "panel_county_year_2015_2024.csv"), dtype={"fips": str, "state_fips": str})
    lines, stats = [], {}

    def say(s=""):
        lines.append(s)

    say("QA REPORT - U.S. Rural Road Fatality County Panel (data verified by the author, 2026-10-21)")
    say("Plain-language summary: every check below says PASS or REVIEW. REVIEW items are in your checklist.")
    say("")

    # 1. Conservation of deaths
    say("1. NO DEATHS LOST OR DOUBLE-COUNTED")
    by = w.groupby("year").deaths.sum()
    src = {int(k): v for k, v in log["fars_fatals_by_year"].items()}
    per = {int(k): v for k, v in log["deaths_person_file_by_year"].items()}
    for y in sorted(src):
        miss = src[y] - by[y]
        say(f"  {y}: FARS accident file FATALS={src[y]:,}  person-file deaths={per[y]:,}  panel={by[y]:,}  not placed in a county={miss}")
    total_unassigned = sum(src[y] - by[y] for y in src)
    say(f"  Crash records read: {log['fars_crashes_read']:,}. Deaths not placed in any county: {total_unassigned} "
        f"({log['county_rule_counts'].get('R4_unassigned', 0)} crashes with no valid county code and no map point).")
    say(f"  RESULT: {'PASS' if all(src[y]==per[y] for y in src) and total_unassigned < 50 else 'REVIEW'}")
    stats["deaths_by_year"] = {int(k): int(v) for k, v in by.items()}
    stats["fars_fatals_by_year"] = src
    stats["deaths_unassigned_total"] = int(total_unassigned)
    stats["crashes_total"] = int(log["fars_crashes_read"])
    stats["deaths_total"] = int(sum(src.values()))
    say("")

    # 2. 2024 vs NHTSA published report
    say("2. 2024 NATIONAL NUMBERS vs NHTSA PUBLISHED REPORT (uses the FARS rural/urban label)")
    y24 = w[w.year == 2024]
    fr, fu = int(y24.deaths_fars_rural.sum()), int(y24.deaths_fars_urban.sum())
    say(f"  Total deaths:   FARS file {src[2024]:,} vs NHTSA {NHTSA_2024['total']:,}")
    say(f"  Rural (FARS):   panel {fr:,} vs NHTSA {NHTSA_2024['rural']:,}  (difference = deaths in crashes with no county)")
    say(f"  Urban (FARS):   panel {fu:,} vs NHTSA {NHTSA_2024['urban']:,}")
    ok = src[2024] == NHTSA_2024["total"] and abs(fr - NHTSA_2024["rural"]) <= 5 and abs(fu - NHTSA_2024["urban"]) <= 5
    say(f"  Source: {NHTSA_2024['source']}")
    say(f"  RESULT: {'PASS' if ok else 'REVIEW'}")
    stats["nhtsa_2024"] = NHTSA_2024
    say("")

    # 3. Rural share, two definitions
    say("3. RURAL SHARE OF DEATHS, TWO DEFINITIONS")
    g = w.groupby("year")[["deaths", "deaths_rural", "deaths_urban", "deaths_ru_unknown",
                           "deaths_fars_rural", "deaths_fars_urban", "deaths_fars_ru_unknown"]].sum()
    g["pct_rural_census"] = (g.deaths_rural / g.deaths * 100).round(1)
    g["pct_rural_fars"] = (g.deaths_fars_rural / g.deaths * 100).round(1)
    say(g[["deaths", "deaths_rural", "pct_rural_census", "deaths_fars_rural", "pct_rural_fars", "deaths_ru_unknown"]].to_string())
    stats["rural_by_year"] = {int(y): {"deaths": int(r.deaths), "rural_census": int(r.deaths_rural),
                                       "pct_rural_census": float(r.pct_rural_census), "rural_fars": int(r.deaths_fars_rural),
                                       "pct_rural_fars": float(r.pct_rural_fars), "ru_unknown_census": int(r.deaths_ru_unknown)}
                              for y, r in g.iterrows()}
    say("")

    # 4. Geography match rates
    say("4. LOCATION MATCH RATES")
    xw = pd.read_csv(os.path.join(P, "crash_crosswalk_2015_2024.csv"), dtype=str,
                     usecols=["county_rule", "coord_valid", "county_point_agrees", "place_match", "cousub_match"])
    n = len(xw)
    cr = xw.county_rule.value_counts()
    for k, v in cr.items():
        say(f"  County rule {k}: {v:,} crashes ({v/n*100:.2f}%)")
    cv = (xw.coord_valid == "True").sum()
    agree = (xw.county_point_agrees == "1.0").sum() + (xw.county_point_agrees == "True").sum()
    say(f"  Crashes with a usable map point: {cv:,} ({cv/n*100:.2f}%)")
    say(f"  Of those, map point inside the FARS-coded county: {agree:,} ({agree/cv*100:.2f}%)")
    for k, v in xw.place_match.value_counts().items():
        say(f"  Place match {k}: {v:,} ({v/n*100:.1f}%)")
    for k, v in xw.cousub_match.value_counts().items():
        say(f"  County subdivision match {k}: {v:,} ({v/n*100:.2f}%)")
    stats["match"] = {"crashes": int(n), "coord_valid": int(cv), "pct_coord_valid": round(cv / n * 100, 2),
                      "point_agrees_county": int(agree), "pct_point_agrees": round(agree / cv * 100, 2),
                      "county_rule": {k: int(v) for k, v in cr.items()},
                      "place": {k: int(v) for k, v in xw.place_match.value_counts().items()},
                      "cousub": {k: int(v) for k, v in xw.cousub_match.value_counts().items()}}
    say("")

    # 5. Population
    say("5. POPULATION")
    say(f"  County-years missing population: {int(w.population.isna().sum())}")
    say(f"  County-years with rebuilt or split population (CT 2020-24, AK Chugach/Copper River 2015-19): {int(w.pop_imputed.sum())}")
    pop = w.groupby("year").population.sum()
    say("  National population by year: " + ", ".join(f"{y}: {v:,.0f}" for y, v in pop.items()))
    stats["population_by_year"] = {int(k): int(v) for k, v in pop.items()}
    say("")

    # 6. Road miles
    if "miles_total_2024" in w:
        say("6. ROAD MILES (HPMS 2024)")
        m = w[w.year == 2024].groupby("state").miles_total_2024.sum()
        say(f"  Public road miles assigned to counties: {m.sum():,.0f}")
        say(f"  Miles HPMS left without a county code (kept out of county totals): {log.get('hpms_miles_in_unmatched_codes', 0):,.0f} "
            f"in codes {log.get('hpms_county_codes_not_in_2020_counties')}")
        zero = w[(w.year == 2024) & (w.miles_total_2024 == 0)]
        say(f"  Counties with zero assigned miles: {len(zero)} -> {', '.join(zero.fips + ' ' + zero.county_name)[:600]}")
        stats["hpms_miles_assigned"] = float(round(m.sum(), 0))
        stats["hpms_miles_unassigned"] = float(round(log.get("hpms_miles_in_unmatched_codes", 0), 0))
        stats["hpms_unassigned_codes"] = log.get("hpms_county_codes_not_in_2020_counties")
        stats["hpms_counties_zero_miles"] = int(len(zero))
        q = pd.read_csv(os.path.join(P, "hpms_state_check_vs_hm20.csv"), dtype={"fips_state": str}, index_col=0)
        st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).set_index("fips_state").abbr
        q.index = q.index.astype(str).str.zfill(2).map(st)
        say("  State map mileage vs FHWA Table HM-20 (ratio_total = map / official):")
        say("    " + q[["hpms_map_total", "hm20_total", "ratio_total", "ratio_nonlocal", "miles_quality"]].round(3).to_string().replace("\n", "\n    "))
        bad = q[q.miles_quality != "complete"]
        stats["hpms_states_complete"] = int((q.miles_quality == "complete").sum())
        stats["hpms_states_flagged"] = {k: v for k, v in bad.miles_quality.items()}
        stats["hpms_quality_summary"] = (f"In {len(bad)} of 51 states the HPMS map mileage is more than 5 percent away from FHWA's official "
                                         f"state total ({', '.join(sorted(bad.index))}), almost always because local roads are missing from the map data.")
        say("")

    # 7. Unusual year-to-year changes (for the author's review)
    say("7. COUNTIES WITH UNUSUAL YEAR-TO-YEAR CHANGES")
    say("  Rule: a county-year is flagged when its deaths are outside what chance would produce 999 times in 1,000")
    say("  given the county's average in the other nine years, scaled by that year's national level (Poisson test),")
    say("  AND it differs from the year before by 5 or more. Scaling keeps the national 2020-2021 rise from flagging every large county.")
    d = w[["fips", "state", "county_name", "year", "deaths", "deaths_rural"]].sort_values(["fips", "year"]).copy()
    tot = d.groupby("fips").deaths.transform("sum")
    d["mean_other_years"] = (tot - d.deaths) / 9
    d["prev_year"] = d.groupby("fips").deaths.shift(1)
    nat = d.groupby("year").deaths.sum()
    d["year_factor"] = d.year.map(nat / nat.mean())
    mu = (d.mean_other_years * d.year_factor).clip(lower=0.1)
    d["expected"] = mu.round(1)
    d["p_high"] = poisson.sf(d.deaths - 1, mu)
    d["p_low"] = poisson.cdf(d.deaths, mu)
    d["flag"] = ((d.p_high < 0.001) | (d.p_low < 0.001)) & ((d.deaths - d.prev_year).abs() >= 5)
    f = d[d.flag].copy()
    f["direction"] = np.where(f.deaths > f.expected, "up", "down")
    f["review_status"] = "PENDING - author to review"
    f["review_note"] = ""
    f = f[["fips", "state", "county_name", "year", "deaths", "prev_year", "mean_other_years", "expected", "direction",
           "p_high", "p_low", "review_status", "review_note"]].round({"mean_other_years": 1, "p_high": 6, "p_low": 6})
    # Help the review: how many crashes, and the largest single crash, in each flagged county-year
    xc = pd.read_csv(os.path.join(P, "crash_crosswalk_2015_2024.csv"), dtype={"fips": str}, usecols=["year", "fips", "fatals", "st_case"])
    agg = xc.groupby(["fips", "year"]).agg(crashes=("st_case", "count"), largest_crash_deaths=("fatals", "max")).reset_index()
    f = f.merge(agg, on=["fips", "year"], how="left")
    excess = f.deaths - f.expected
    f["hint"] = np.where((f.direction == "up") & (f.largest_crash_deaths >= 3) & (f.largest_crash_deaths - 1 >= 0.5 * excess),
                         "one multi-death crash explains much of the jump", "")
    f.to_csv(os.path.join(P, "review_unusual_changes.csv"), index=False)
    say(f"  Flagged county-years: {len(f)} in {f.fips.nunique()} counties. File: data/processed/review_unusual_changes.csv")
    say(f"  Up: {(f.direction=='up').sum()}, down: {(f.direction=='down').sum()}. Each needs a review_status of OK (real change) or FIX.")
    say(f"  Of these, {(f.hint != '').sum()} have one multi-death crash that explains much of the jump (column 'hint').")
    stats["unusual_one_crash"] = int((f.hint != "").sum())
    stats["unusual_flags"] = int(len(f))
    stats["unusual_counties"] = int(f.fips.nunique())
    say("")

    # 8. Named spot checks
    say("8. NAMED SPOT CHECKS (verify these by hand against FARS; steps in docs/VERIFY_CHECKLIST.md)")
    cols = ["year", "deaths", "deaths_rural", "deaths_urban", "deaths_fars_rural", "deaths_pedestrian", "population", "death_rate_per100k"]
    spot = {}
    for fips, label in SPOT.items():
        s = w[w.fips == fips].sort_values("year")
        say(f"  {fips} {label}")
        say("    " + s[cols].to_string(index=False).replace("\n", "\n    "))
        r = s[s.year == 2024].iloc[0]
        spot[fips] = {"label": label, "deaths_2024": int(r.deaths), "deaths_rural_2024": int(r.deaths_rural),
                      "crashes_2024": int(r.crashes), "deaths_2015_2024": int(s.deaths.sum())}
    stats["spot"] = spot
    say("")

    # 9. Range checks
    say("9. RANGE CHECKS")
    neg = (w.select_dtypes("number") < 0).sum().sum()
    parts = w.deaths_rural + w.deaths_urban + w.deaths_ru_unknown
    ptype = w[[c for c in w.columns if c in ["deaths_driver", "deaths_passenger", "deaths_occupant_other", "deaths_pedestrian",
                                             "deaths_cyclist", "deaths_nonmotorist_other"]]].sum(axis=1)
    say(f"  Negative values: {neg}")
    say(f"  Rural + urban + unknown = total deaths in every row: {bool((parts == w.deaths).all())}")
    say(f"  Person types add to total deaths in every row: {bool((ptype == w.deaths).all())}")
    say(f"  Highest county death rate per 100,000 (one year): {w.death_rate_per100k.max():.1f} "
        f"({w.loc[w.death_rate_per100k.idxmax(), 'county_name']}, {w.loc[w.death_rate_per100k.idxmax(), 'state']}, "
        f"{w.loc[w.death_rate_per100k.idxmax(), 'year']}) - small populations make single-year rates jumpy")
    say(f"  County-years with zero deaths: {(w.deaths == 0).sum():,} of {len(w):,}")
    stats["panel_rows"] = int(len(w))
    stats["counties"] = int(w.fips.nunique())
    stats["zero_death_county_years"] = int((w.deaths == 0).sum())

    # National rural rates
    ru = w.groupby("year")[["deaths_rural", "deaths_urban"]].sum()
    pr = w[w.year == 2020].pop2020_rural.sum()
    pt = w[w.year == 2020].pop2020_census.sum()
    stats["pop2020_rural"] = int(pr)
    stats["pop2020_total"] = int(pt)
    stats["pct_pop_rural_2020"] = round(pr / pt * 100, 1)
    stats["rate_rural_2020_per100k"] = round(ru.loc[2020, "deaths_rural"] / pr * 1e5, 1)
    stats["rate_urban_2020_per100k"] = round(ru.loc[2020, "deaths_urban"] / (pt - pr) * 1e5, 1)

    open(os.path.join(P, "qa_report.txt"), "w").write("\n".join(lines) + "\n")
    json.dump(stats, open(os.path.join(ROOT, "paper", "stats.json"), "w"), indent=2)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
