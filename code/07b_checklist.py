#!/usr/bin/env python3
"""
07b_checklist.py - Write docs/VERIFY_CHECKLIST.md, the author's hands-on checklist,
with this release's real files, rows, and numbers filled in from the data.

PLAIN-LANGUAGE NOTE: You do not run this; Claude does. You open the checklist it writes.
"""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))


def n(x):
    return f"{int(x):,}"


def main():
    w = pd.read_csv(os.path.join(P, "panel_county_year_2015_2024.csv"), dtype={"fips": str, "state_fips": str})
    w["row"] = w.index + 2  # spreadsheet row number (header is row 1)
    flags = pd.read_csv(os.path.join(P, "review_unusual_changes.csv"), dtype={"fips": str})
    r = S["rural_by_year"]
    v = S["validation"]["overall_deaths"]

    def county_item(fips, year, why):
        x = w[(w.fips == fips) & (w.year == year)].iloc[0]
        st, cc = int(fips[:2]), int(fips[2:])
        return (f"- [ ] **{x.county_name}, {x.state} ({year})** - {why}. In `data/processed/panel_county_year_2015_2024.csv`, row {x.row:,}: "
                f"`deaths` = **{int(x.deaths)}**, `crashes` = **{int(x.crashes)}**, `deaths_rural` = {int(x.deaths_rural)}, `deaths_pedestrian` = {int(x.deaths_pedestrian)}. "
                f"Check: open `accident.csv` from the FARS {year} file, filter `STATE` = {st} and `COUNTY` = {cc}"
                + (" (also COUNTY = 113, the old Shannon County code)" if fips == "46102" else "")
                + (" (also COUNTY = 261, Valdez-Cordova, whose crashes are placed by map point)" if fips in ("02063", "02066") else "")
                + f". Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___")

    known = [("29077", 2024, "your home county"), ("29077", 2015, "your home county, first year"),
             ("29105", 2024, "a rural Ozarks county you know"), ("29043", 2024, "Christian County, next to Springfield"),
             ("29213", 2024, "Taney County, Branson tourism traffic")]
    known = [k for k in known if ((w.fips == k[0]) & (w.year == k[1])).any()]
    hard = [("46102", 2022, "FARS still uses the old Shannon County code; tests rule R2"),
            ("09001", 2024, "Connecticut legacy county; tests the town-sum population"),
            ("02066", 2016, "Copper River, Alaska: split from Valdez-Cordova in 2019, so its 2016 crashes are placed by map point (rule R3)")]
    top = w[w.year == 2024].sort_values("deaths", ascending=False).iloc[0]
    hi_rate = w[(w.year == 2024) & (w.population >= 10000)].sort_values("death_rate_per100k", ascending=False).iloc[0]
    extremes = [(top.fips, 2024, "the most deaths of any county in 2024"),
                (hi_rate.fips, 2024, "the highest 2024 death rate among counties of 10,000+ people")]
    rnd = w[w.deaths > 0].sample(5, random_state=20261021)
    randoms = [(x.fips, int(x.year), "random row (seed 20261021)") for x in rnd.itertuples()]

    fl_top = flags.sort_values("p_high").head(8) if len(flags) else flags

    lines = f"""# Your verification checklist

*Plain-language version: before anything goes public under your name, you check it. Every file, row, and number below is real and comes from this build. Total time: about 3 to 4 hours. Split it into sittings; Part 4 can be done a few counties at a time. Tick each box and write what you found on the line.*

*The pre-publication check (`tools/publish_gate.py`) handles the mechanical items. These are yours.*

**What you need open:** the project folder; Excel or Google Sheets; the FARS files, downloaded free from https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/ (open a year, then `National`, then the `FARS20xxNationalCSV.zip` file, unzip it, and open `accident.csv`).

## Part 1: The results rebuild (15 to 30 min)

Pick one:
- [ ] **Option A, ask Claude.** In a new chat with Opus 5.5 or Fable 5, attach the project folder and say: "Re-run this pipeline from scratch following the README, then give me the national deaths by year and the 2024 rural deaths under both definitions." Compare with these numbers. They should match exactly:
  - Deaths by year in the FARS files: {", ".join(f"{y}: {n(c)}" for y, c in S["fars_fatals_by_year"].items())}
  - 2024 rural deaths, Census map: {n(r["2024"]["rural_census"])}; FARS label: {n(r["2024"]["rural_fars"])}
- [ ] **Option B, run it yourself** (needs Python): open a terminal in the project folder, paste the commands from the README "Run it" section one by one. The last lines of `python code/03_qa.py` should show the same numbers as above.

## Part 2: National numbers against NHTSA (15 min)

- [ ] Open NHTSA's report *Traffic Safety Facts 2024 Data: Rural/Urban Traffic Fatalities* (DOT HS 813 828): https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813828 . Find the sentence "Of 39,254 traffic fatalities in 2024, 16,006 (41%) were in rural areas and 22,905 (58%) were in urban areas."
  - Our FARS file total for 2024: **{n(S["fars_fatals_by_year"]["2024"])}**. Match? ___
  - Our 2024 rural deaths using the FARS label: **{n(r["2024"]["rural_fars"])}** (the difference from 16,006 is deaths in crashes that could not be placed in a county; see `data/processed/qa_report.txt` section 2). OK? ___
- [ ] Open NHTSA's FARS state data page https://www-fars.nhtsa.dot.gov/States/StatesFatalitiesFatalityRates.aspx and check the national total for two other years, say 2019 and 2022. Ours: 2019 **{n(S["fars_fatals_by_year"]["2019"])}**, 2022 **{n(S["fars_fatals_by_year"]["2022"])}**. If NHTSA's page shows an older (preliminary) number, note it: FARS files are revised after first release. ___

## Part 3: County rows by hand (45 to 60 min)

For each row: find it in the panel file, then count it in the FARS `accident.csv` for that year. A tip for Excel: use Data > Filter, filter `STATE` and `COUNTY`, and the status bar shows the count and the sum of `FATALS` when you select that column.

FARS uses numeric codes: the state code is the first two digits of the county FIPS code without the leading zero, and the county code is the last three digits without leading zeros (Greene County, MO is FIPS 29077, so STATE = 29 and COUNTY = 77).

**Counties you know personally:**
{chr(10).join(county_item(*k) for k in known)}

**Hard cases (the join rules at work):**
{chr(10).join(county_item(*k) for k in hard)}

**Extreme values:**
{chr(10).join(county_item(*k) for k in extremes)}

**Random rows:**
{chr(10).join(county_item(*k) for k in randoms)}

If a count differs by one or two, check `n_crashes_point_in_other_county` and `county_rule` in `data/processed/crash_crosswalk_2015_2024.csv` (filter by `fips`) before calling it an error, and write it down. Claude will trace any difference you find.

## Part 4: Counties with unusual changes (60 to 90 min; can be spread over several days)

Your stated role includes reviewing every county with an unusual change between years. The build flagged **{len(flags)} county-years in {flags.fips.nunique() if len(flags) else 0} counties** (`data/processed/review_unusual_changes.csv`). For each, decide: **OK** (a real change, for example one multi-death crash, a new highway segment, a known event) or **FIX** (looks like a coding error). Write OK or FIX in `review_status` and a few words in `review_note`.

The file already helps: `crashes` is the number of fatal crashes that year, `largest_crash_deaths` is the deadliest single crash, and `hint` marks the rows where one multi-death crash explains much of the jump (usually OK after a quick look). `expected` is what the county's other years predict, adjusted for the national level that year. For the rest, filter the crosswalk file to that `fips` and `year`, filter the crosswalk file to that `fips` and `year` look at the crashes (road class, map point), and decide. A local news search for the county and year often settles it. The eight strongest flags:

| County | Year | Deaths | Year before | Expected | Largest single crash |
|---|---|---|---|---|---|
{chr(10).join(f"| {x.county_name}, {x.state} ({x.fips}) | {x.year} | {int(x.deaths)} | {'' if pd.isna(x.prev_year) else int(x.prev_year)} | {x.expected} | {int(x.largest_crash_deaths)} |" for x in fl_top.itertuples())}

- [ ] Every row in `review_unusual_changes.csv` has OK or FIX. Number marked FIX: ___ (Claude will investigate each FIX.)

## Part 5: The validation study (20 min)

- [ ] Open `paper/validation_tables/disagreement_sample.csv`: 40 crashes from 2024 where FARS and the Census map disagree. Click the Google Maps link for at least 10. For each, write in `your_judgment` whether the place looks rural or urban to you. This is a check on the map points, not on FARS. ___ of 10 looked like the Census map's answer.
- [x] The three manuscript checks are resolved: RUR_URB follows "FHWA-approved adjusted Census boundaries of small urban and urbanized areas" (FARS Analytical User's Manual, DOT HS 813 794, April 2026, element C12A); the 2020 urban area criteria are 87 FR 16706 (March 24, 2022) and 87 FR 80114 (December 29, 2022). Spot-check them if you like.

## Part 6: Your decisions (10 min)

The build made these choices provisionally. Agree or change each one.

- [ ] **Release timing for 2024.** FARS 2024 is the preliminary Annual Report File; NHTSA usually posts the Final File about a year after the first release (around April 2027).
  - A (recommended): release v1.0 now with the 2024 Annual Report File clearly labeled, then v1.0.1 when the Final File appears. You get a DOI now; the update is a routine version.
  - B: wait for the 2024 Final File (around April 2027).
  - Your choice: ___
- [ ] **How to describe the decline in the FARS rural share.** The data show the FARS label's rural share falling much faster than the fixed-map share. The manuscript calls the boundary change "one plausible mechanism" and keeps it as a hypothesis until you confirm how RUR_URB is assigned (Part 5).
  - A (recommended): keep it as a hypothesis unless the FARS manual confirms it.
  - B: state it as the cause (only if the manual and FHWA guidance confirm it).
  - Your choice: ___
- [ ] **Map figure.** Figure 3 shows deaths per 100,000 residents (all deaths), the standard NHTSA measure. A rural-only rate (rural deaths per rural resident) is possible but misleading for counties crossed by long highways with few rural residents.
  - A (recommended): keep the all-deaths rate on the map; rural share is a separate atlas layer.
  - B: add a rural-only rate layer to the atlas with a warning.
  - Your choice: ___
- [ ] **Road miles where local roads are incomplete.** {S.get("hpms_quality_summary", "Some states' map data lack local roads.")}
  - A (recommended): keep the miles with the `miles_quality_state` flag; the atlas hides the deaths-per-mile layer for flagged states.
  - B: drop local and total miles for flagged states (keep arterials and collectors only).
  - Your choice: ___

## Part 7: Before it goes public (20 to 30 min)

- [ ] Rewrite in your own words: the "In plain terms" paragraph in `README.md`, the "How it connects to your work" paragraph in `docs/START_HERE.md`, and the text of the preprint (`code/preprint_template.tex`; engrXiv requires the prose to be your own). Claude can do it with you line by line.
- [ ] Your name, ORCID, affiliation, and email are correct in `AUTHORS.json`. (Email is used for the preprint and commits only; it is not printed in the README.)
- [ ] You have read `docs/LIMITATIONS.md` and agree with it.
- [ ] You have read `docs/JOIN_RULES.md` and agree with every rule (these are your rules).
- [ ] Claude regenerates everything with `--final` and `python tools/publish_gate.py .` passes.

**When every box is ticked, reply to Claude in your own words that you have checked the package and approve publishing.**
"""
    open(os.path.join(ROOT, "docs", "VERIFY_CHECKLIST.md"), "w").write(lines)
    print("checklist written;", len(flags), "flags")


if __name__ == "__main__":
    main()
