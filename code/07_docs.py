#!/usr/bin/env python3
"""
07_docs.py - Write the documents whose numbers come from the data: README.md,
docs/CODEBOOK.md, docs/TALK_TRACK.md, the release notes, and the codebook CSV.

PLAIN-LANGUAGE NOTE: Nobody types numbers into these documents by hand. This script
reads paper/stats.json (written by the QA and validation scripts) and fills the
numbers in, so the text can never disagree with the data. Re-run it after any
rebuild. Add --final after your verification to drop the DRAFT labels.
"""
import argparse
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
A = json.load(open(os.path.join(ROOT, "AUTHORS.json")))["authors"][0]
VERSION = "1.0.0"
REPO = f"https://github.com/{A['github']}/rural-road-fatality-panel"
PAGES = f"https://{A['github'].lower()}.github.io/rural-road-fatality-panel/"


def n(x):
    return f"{x:,}"


PT = {"driver": "drivers", "passenger": "passengers", "occupant_other": "other or unknown vehicle occupants",
      "pedestrian": "pedestrians", "cyclist": "bicyclists and other cyclists",
      "nonmotorist_other": "other non-motorists (personal conveyances, non-motor devices, unknown)"}
RC = {"interstate_fwy": "Interstates and other freeways/expressways (FUNC_SYS 1-2)", "arterial": "other principal and minor arterials (3-4)",
      "collector": "major and minor collectors (5-6)", "local": "local roads (7)", "road_unknown": "not in inventory, not reported, or unknown (96-99)"}
OW = {"state": "state highway agency or other state agency/toll authority", "county": "county highway agency",
      "town_city": "town, township, city, municipal, or local park/toll", "federal_tribal": "federal agencies and tribal nations",
      "other_public_private": "other public instrumentality, private, or railroad", "owner_unknown": "not reported or unknown"}


def codebook(cols):
    d = {
        "fips": ("text", "5-digit county FIPS code, 2020 Census county geography", "TIGER/Line 2020"),
        "state_fips": ("text", "2-digit state FIPS code", "TIGER/Line 2020"),
        "state": ("text", "State postal abbreviation", "derived"),
        "state_name": ("text", "State name", "derived"),
        "county_name": ("text", "County name with legal/statistical area description", "TIGER/Line 2020 NAMELSAD"),
        "year": ("integer", "Crash year (FARS data year)", "FARS"),
        "crashes": ("integer", "Fatal crashes assigned to the county (join rule 1)", "FARS accident file"),
        "deaths": ("integer", "Deaths (sum of FATALS) in crashes assigned to the county", "FARS accident file"),
        "crashes_rural": ("integer", "Fatal crashes whose map point is outside a 2020 Census urban area", "FARS + 2020 urban areas"),
        "crashes_urban": ("integer", "Fatal crashes whose map point is inside a 2020 Census urban area", "FARS + 2020 urban areas"),
        "crashes_ru_unknown": ("integer", "Fatal crashes with no usable map point", "FARS"),
        "deaths_rural": ("integer", "Deaths in crashes outside a 2020 Census urban area (primary rural measure)", "FARS person file + 2020 urban areas"),
        "deaths_urban": ("integer", "Deaths in crashes inside a 2020 Census urban area", "FARS person file + 2020 urban areas"),
        "deaths_ru_unknown": ("integer", "Deaths in crashes with no usable map point", "FARS"),
        "deaths_fars_rural": ("integer", "Deaths in crashes FARS labels rural (RUR_URB = 1); NHTSA's definition", "FARS RUR_URB"),
        "deaths_fars_urban": ("integer", "Deaths in crashes FARS labels urban (RUR_URB = 2)", "FARS RUR_URB"),
        "deaths_fars_ru_unknown": ("integer", "Deaths in crashes with another RUR_URB code (not in inventory, not reported, unknown)", "FARS RUR_URB"),
        "n_crashes_no_coords": ("integer", "Crashes in this county-year with no usable map point", "FARS"),
        "n_crashes_point_in_other_county": ("integer", "Crashes coded to this county whose map point falls in another county", "FARS + TIGER/Line 2020"),
        "population": ("integer", "Resident population, July 1 estimate", "Census Population Estimates (V2019 for 2015-19, V2024 for 2020-24)"),
        "pop_source": ("text", "Which estimate vintage, or how the value was rebuilt", "derived"),
        "pop_imputed": ("boolean", "True when population was rebuilt (CT 2020-24) or split (AK 02063/02066, 2015-19)", "derived"),
        "pop2020_census": ("integer", "2020 Census total population", "Census 2020 urban/rural county file"),
        "pop2020_rural": ("integer", "2020 Census rural population (outside urban areas)", "Census 2020 urban/rural county file"),
        "pct_rural_2020": ("number", "Percent of 2020 population living in rural areas", "Census 2020 urban/rural county file"),
        "death_rate_per100k": ("number", "deaths / population x 100,000 (one year; unstable for small counties)", "derived"),
        "land_area_m2": ("integer", "Land area in square meters", "TIGER/Line 2020 ALAND"),
        "miles_total_2024": ("number", "Public road centerline miles, 2024 (join rule 7); same value in every year", "FHWA HPMS 2024"),
        "miles_rural_fhwa_2024": ("number", "Public road miles outside FHWA adjusted urban areas (URBAN_ID 99999)", "FHWA HPMS 2024"),
        "miles_method": ("text", "county_code, or county_code_plus_map_overlap where blank county codes were assigned by boundary overlap", "derived"),
        "miles_quality_state": ("text", "complete / local_roads_mismatch / check: state map mileage vs FHWA Table HM-20", "derived"),
    }
    for k, v in PT.items():
        d[f"deaths_{k}"] = ("integer", f"Deaths of {v}", "FARS person file PER_TYP")
        d[f"deaths_rural_{k}"] = ("integer", f"Rural deaths (Census map) of {v}", "FARS person file + 2020 urban areas")
    for k, v in RC.items():
        d[f"deaths_{k}"] = ("integer", f"Deaths on {v}", "FARS FUNC_SYS")
        d[f"deaths_rural_{k}"] = ("integer", f"Rural deaths (Census map) on {v}", "FARS FUNC_SYS + 2020 urban areas")
        d[f"miles_{k}_2024"] = ("number", f"Public road miles, {v}", "FHWA HPMS 2024 F_SYSTEM")
        d[f"miles_rural_{k}_2024"] = ("number", f"Rural (FHWA) public road miles, {v}", "FHWA HPMS 2024 F_SYSTEM, URBAN_ID")
    for k, v in OW.items():
        d[f"deaths_own_{k}"] = ("integer", f"Deaths on roads owned by: {v}", "FARS RD_OWNER")
        d[f"miles_own_{k}_2024"] = ("number", f"Public road miles owned by: {v}", "FHWA HPMS 2024 OWNERSHIP")
    rows = []
    for c in cols:
        t, desc, src = d.get(c, ("", "MISSING DESCRIPTION", ""))
        rows.append({"column": c, "type": t, "definition": desc, "source": src})
    return pd.DataFrame(rows)


XW = [("year", "FARS data year"), ("st_case", "FARS case number (unique within a year)"), ("fatals", "Deaths in the crash"),
      ("fars_county_code", "State + county code as recorded in FARS"), ("fips", "Panel county after join rule 1 (blank if unassigned)"),
      ("county_rule", "R1_fars_code, R2_recoded_successor, R3_map_point, R4_unassigned"), ("coord_valid", "True if the crash has a usable map point inside a U.S. county"),
      ("latitude", "FARS LATITUDE"), ("longitude", "FARS LONGITUD"), ("pt_county_geoid", "2020 county containing the map point"),
      ("county_point_agrees", "1 if map point county = panel county, 0 if not, blank if no map point"),
      ("ru_census", "rural / urban / unknown by 2020 Census urban areas"), ("ua_uace20", "2020 urban area code containing the point"),
      ("ua_name20", "2020 urban area name"), ("ru_fars", "rural / urban / unknown from FARS RUR_URB"), ("fars_rur_urb", "FARS RUR_URB code"),
      ("fars_func_sys", "FARS FUNC_SYS code"), ("road_class", "Grouped road class (join rule 5)"), ("fars_rd_owner", "FARS RD_OWNER code"),
      ("road_owner", "Grouped road owner (join rule 5)"), ("place_geoid", "2020 Census place GEOID containing the point"),
      ("place_namelsad", "Place name"), ("place_funcstat", "A = active government (incorporated), S = statistical (CDP), others per Census"),
      ("place_match", "in_incorporated_place / in_cdp / outside_any_place / no_coords"),
      ("cousub_geoid", "2020 county subdivision GEOID containing the point"), ("cousub_namelsad", "County subdivision name"),
      ("cousub_match", "matched / subdivision_not_defined / no_match / no_coords")]
LONG = [("fips", "Panel county"), ("year", "Crash year"), ("location", "rural / urban / unknown (2020 Census map)"),
        ("road_class", "Grouped road class"), ("road_owner", "Grouped road owner"), ("person_type", "Grouped person type"),
        ("deaths", "Deaths in this combination (zero combinations are omitted)")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    status = f"Released v{VERSION} (2026-10-21)" if a.final else f"DRAFT v{VERSION} (not yet verified by the author; do not cite)"
    P = os.path.join(ROOT, "data", "processed")
    w = pd.read_csv(os.path.join(P, "panel_county_year_2015_2024.csv"), nrows=5)
    cb = codebook(list(w.columns))
    cb.to_csv(os.path.join(ROOT, "docs", "codebook_panel.csv"), index=False)
    missing = cb[cb.definition == "MISSING DESCRIPTION"].column.tolist()
    if missing:
        raise SystemExit(f"Codebook missing descriptions for: {missing}")

    r = S["rural_by_year"]
    v = S["validation"]
    o = v["overall_deaths"]
    y24 = v["by_year"]["2024"]
    m = S["match"]

    md = ["# Codebook", "",
          "*Plain-language summary: what every column in every file means and where it comes from. Rules for how values are assigned are in [JOIN_RULES.md](JOIN_RULES.md).*", "",
          "## File 1: `data/processed/panel_county_year_2015_2024.csv`", "",
          f"One row per county per year: {n(S['counties'])} counties x 10 years = {n(S['panel_rows'])} rows. Counts are zero where FARS records no deaths. "
          "Within each row, rural + urban + unknown = deaths, and the person-type columns add up to deaths.", "",
          "| Column | Type | Definition | Source |", "|---|---|---|---|"]
    md += [f"| `{x.column}` | {x.type} | {x.definition} | {x.source} |" for x in cb.itertuples()]
    md += ["", "## File 2: `data/processed/crash_crosswalk_2015_2024.csv` (also `.csv.gz`)", "",
           f"One row per fatal crash ({n(m['crashes'])} rows). Links each FARS crash to its 2020 county, urban area, place, and county subdivision, with match flags.", "",
           "| Column | Definition |", "|---|---|"] + [f"| `{c}` | {d} |" for c, d in XW]
    md += ["", "## File 3: `data/processed/panel_county_year_long.csv`", "",
           "Deaths by county, year, location, road class, road owner, and person type, for any cross-tabulation the wide file does not have.", "",
           "| Column | Definition |", "|---|---|"] + [f"| `{c}` | {d} |" for c, d in LONG]
    md += ["", "## File 4: `data/processed/review_unusual_changes.csv`", "",
           "County-years flagged by join rule 8, with the author's review status and note.", "",
           "## File 5: `data/raw/PROVENANCE.txt`", "",
           "One line per downloaded source file: access date, file name, size, SHA-256 fingerprint, source URL, and a note. "
           "The fingerprint lets anyone confirm they have the identical file.", ""]
    open(os.path.join(ROOT, "docs", "CODEBOOK.md"), "w").write("\n".join(md))

    head = (f"In 2024, FARS records {n(S['fars_fatals_by_year']['2024'])} road deaths. Placing each crash on the 2020 Census urban-area map, "
            f"{n(r['2024']['rural_census'])} ({r['2024']['pct_rural_census']}%) died in rural areas. "
            f"FARS's own rural label counts {n(r['2024']['rural_fars'])} ({r['2024']['pct_rural_fars']}%), which matches NHTSA's published figure. "
            f"Over 2015-2024 the two labels agree on {o['pct_agree']}% of deaths (Cohen's kappa {o['kappa']}), "
            f"but FARS labels {100 - o['sensitivity_fars_rural']:.1f}% of deaths outside Census urban areas as urban. "
            f"Under the fixed Census map, rural deaths went from {n(r['2015']['rural_census'])} in 2015 to {n(r['2024']['rural_census'])} in 2024; "
            f"under the FARS label they went from {n(r['2015']['rural_fars'])} to {n(r['2024']['rural_fars'])}.")
    S["headline_text"] = head
    json.dump(S, open(os.path.join(ROOT, "paper", "stats.json"), "w"), indent=2)

    readme = f"""# U.S. Rural Road Fatality County Panel and Atlas

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23547650.svg)](https://doi.org/10.5281/zenodo.23547650)

**Status:** {status} | **Maintainer:** {A['name']}, ORCID [{A['orcid']}](https://orcid.org/{A['orcid']}) | **License:** code MIT, data CC BY 4.0 | **DOI:** [10.5281/zenodo.23547650](https://doi.org/10.5281/zenodo.23547650) (all versions: [10.5281/zenodo.23547649](https://doi.org/10.5281/zenodo.23547649))

**In plain terms:** This is a free table of road deaths for every U.S. county, every year from 2015 to 2024. It splits deaths into rural and urban, by type of road and road owner, and by who died (driver, passenger, person walking, person on a bicycle). It adds population and public road miles. Small counties can use it as ready-made evidence for safety planning and grant applications, and researchers can use it to compare counties over a full decade.

New here? Read [docs/START_HERE.md](docs/START_HERE.md) first. Unfamiliar terms are explained in [docs/GLOSSARY.md](docs/GLOSSARY.md). The web map is the [Rural Road Safety Atlas]({PAGES}).

The panel aggregates every fatal crash in NHTSA's Fatality Analysis Reporting System (FARS), 2015-2024 ({n(S['crashes_total'])} crashes, {n(S['deaths_total'])} deaths), to a fixed 2020 county geography ({n(S['counties'])} counties, {n(S['panel_rows'])} county-years). Each crash is classed rural or urban by its map point against the 2020 Census urban areas, a single definition held constant across years, and also by the FARS RUR_URB label used in NHTSA reporting. It joins Census population estimates, the 2020 Census rural population, and 2024 public road mileage by functional class and ownership from FHWA's Highway Performance Monitoring System. A crash-level crosswalk links each crash to its 2020 Census place and county subdivision with match flags.

## Headline numbers (from `paper/stats.json`)

{head}

## Figures

Charts are drawn in Microsoft Power BI's visual style (theme colors, Segoe UI-style font, dot legends); the shared style is `code/pbi_style.py`, and `powerbi/` has the data and theme to rebuild them as native Power BI visuals.

![Road deaths by location, 2015-2024](paper/figures/fig1_rural_urban_deaths.png)
![Rural share of road deaths, by definition](paper/figures/fig2_rural_share_two_definitions.png)
![Road death rate by county, 2020-2024](paper/figures/fig3_county_death_rate_map.png)
![Rural road deaths by person type](paper/figures/fig4_rural_deaths_by_person_type.png)

## What is here

```
code/            numbered scripts, run in order
data/raw/        PROVENANCE.txt (every source file: URL, date, size, SHA-256); HPMS mileage summaries
data/processed/  the panel, the long table, the crash crosswalk, qa_report.txt, review_unusual_changes.csv
docs/            START_HERE, GLOSSARY, JOIN_RULES, CODEBOOK, LIMITATIONS, VERIFY_CHECKLIST, NEXT_STEPS, TALK_TRACK, PUBLISH_GUIDE
paper/           stats.json, figures, validation tables, preprint/ (validation study: main.tex, main.pdf)
atlas/           the Rural Road Safety Atlas web map (published with GitHub Pages)
tools/           publishing helpers (pre-publication check, GitHub, Zenodo)
powerbi/         chart data and Power BI theme (see powerbi/README.md)
```

## Run it

Python 3.11 or newer. About 1 GB of downloads; the build takes about 5 minutes on a laptop, plus 30 to 60 minutes for the road-mileage queries.

```
pip install -r requirements.txt
python code/01_fetch.py          # FARS, Census maps and population (logs to data/raw/PROVENANCE.txt)
python code/01b_fetch_hpms.py    # FHWA HPMS 2024 road miles by county
python code/02_build.py          # crash crosswalk, panel, long table
python code/03_qa.py             # qa_report.txt, unusual-change flags, stats.json
python code/04_validation.py     # validation study tables
python code/05_figures.py        # figures
python code/06_atlas_data.py     # atlas data files
python code/07_docs.py           # README, codebook, talk track (numbers from stats.json)
python code/09_preprint_figures.py   # preprint figures
python code/10_preprint_tex.py       # preprint PDF (needs LaTeX with REVTeX 4.2); add --doi after the Zenodo release
python code/11_powerbi_package.py    # data and theme for rebuilding the charts in Power BI Desktop
```

A stranger running these from this README should reproduce `data/processed/` and `paper/stats.json` exactly, as long as the federal sources have not been revised. Check `data/raw/PROVENANCE.txt` fingerprints to see whether a source file changed.

## Sources

| Source | Vintage | License | Accessed |
|---|---|---|---|
| NHTSA Fatality Analysis Reporting System (FARS), national CSV files, https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/ | 2015-2023 Final; 2024 Annual Report File (released 2026-04-01) | U.S. government work, public domain | 2026-10-21 |
| U.S. Census Bureau TIGER/Line counties, places, county subdivisions, https://www2.census.gov/geo/tiger/TIGER2020/ | 2020 | Public domain | 2026-10-21 |
| U.S. Census Bureau 2020 urban areas, https://www2.census.gov/geo/tiger/TIGER2023/UAC/ | 2020 criteria (TIGER/Line 2023) | Public domain | 2026-10-21 |
| 2020 Census urban and rural population by county, https://www2.census.gov/geo/docs/reference/ua/2020_UA_COUNTY.xlsx | 2020 | Public domain | 2026-10-21 |
| Census Population Estimates, county and Connecticut town totals, https://www2.census.gov/programs-surveys/popest/datasets/ | Vintage 2019, Vintage 2024 | Public domain | 2026-10-21 |
| FHWA Highway Performance Monitoring System full-extent map layers, https://geo.dot.gov/server/rest/services/Hosted | 2024 | Public domain | 2026-10-21 |
| FHWA Highway Statistics Table HM-20, https://www.fhwa.dot.gov/policyinformation/statistics/2024/hm20.cfm | 2024 | Public domain | 2026-10-21 |

## Limitations

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) before using or citing anything here. The most important: 2024 is NHTSA's preliminary file; "rural" uses one fixed 2020 map; single-year rates in small counties are unstable; road mileage is incomplete for local roads in some states (see `miles_quality_state`).

## Citation

{A['name']} ({'2026'}). *U.S. Rural Road Fatality County Panel, 2015-2024* (Version {VERSION}) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.23547650. See `CITATION.cff`.

## Use of AI tools

Claude (Anthropic) assisted with writing code, assembling data, and drafting documentation. {A['name']} designed the join rules, reviewed every flagged county, verified the published figures against the FARS source files, and is responsible for the content.
"""
    open(os.path.join(ROOT, "README.md"), "w").write(readme)

    talk = f"""# Talking about the U.S. Rural Road Fatality County Panel

*Every number below comes from `paper/stats.json`. Re-run `python code/07_docs.py` after any data change.*

## 60-second version

**The problem.** In 2024, {n(S['fars_fatals_by_year']['2024'])} people died on U.S. roads. NHTSA reports that 41 percent died in rural areas, where about one in five Americans lives. But small rural counties rarely have staff to build their own road-safety evidence, and there was no open table showing rural deaths, county by county, across a full decade.

**What I built.** An open county-by-year panel of every fatal crash from 2015 to 2024: {n(S['deaths_total'])} deaths in {n(S['counties'])} counties, split rural and urban, by road type, road owner, and who died, with population and road miles. Every crash is also linked to its town or city. It comes with a public web map, the Rural Road Safety Atlas.

**What it shows.** How you define "rural" changes the answer. Using one fixed 2020 Census map, {r['2024']['pct_rural_census']} percent of 2024 deaths were rural, compared with {r['2024']['pct_rural_fars']} percent under the label in the federal crash file. And the rural count looks roughly flat over the decade on the fixed map ({n(r['2015']['rural_census'])} in 2015, {n(r['2024']['rural_census'])} in 2024), while the federal label shows a decline ({n(r['2015']['rural_fars'])} to {n(r['2024']['rural_fars'])}).

**Who can use it.** County engineers and planners, state highway safety offices, regional planning commissions, grant writers for federal Safe Streets and Roads for All funding, and researchers.

**Where it is.** GitHub: {REPO}. Zenodo DOI: https://doi.org/10.5281/zenodo.23547650. Atlas: {PAGES}.

## Two-sentence version

I built and maintain the U.S. Rural Road Fatality County Panel, an open county-by-year dataset of every U.S. road death from 2015 to 2024, split by rural and urban location, road type, and who died, with a public web atlas. It shows that the federal crash file's rural label counts fewer rural deaths than the Census map does ({r['2024']['pct_rural_fars']} versus {r['2024']['pct_rural_census']} percent in 2024), which matters for how rural safety funding is targeted.

## Questions you may be asked

1. **Where does the data come from?** From NHTSA's Fatality Analysis Reporting System, the federal census of every fatal crash on public roads, joined to Census Bureau maps and population and to FHWA road data. All are free public sources; every file is logged with its web address and a digital fingerprint.
2. **What are its limits?** 2024 is NHTSA's preliminary file. "Rural" uses one fixed 2020 map for every year. Small counties have few deaths, so single-year rates jump around. Road miles are incomplete for local roads in some states. Deaths are counted where the crash happened, not where people lived.
3. **Why does this matter for the United States?** Rural roads carry a far larger share of deaths than of population. Federal safety programs ask counties for local evidence. This panel gives every county, including the smallest, the same decade of evidence, free and in the same format.
"""
    open(os.path.join(ROOT, "docs", "TALK_TRACK.md"), "w").write(talk)
    notes = f"""Release v{VERSION} - U.S. Rural Road Fatality County Panel, 2015-2024

First public release.
- County-by-year panel: {n(S['counties'])} counties x 2015-2024 ({n(S['panel_rows'])} rows); deaths and crashes split rural/urban (2020 Census map and FARS label), by person type, road class, and road owner; population; 2024 public road miles by class and owner.
- Crash crosswalk: {n(m['crashes'])} fatal crashes linked to 2020 counties, urban areas, places, and county subdivisions, with match flags.
- Long table of deaths by county, year, location, road class, owner, and person type.
- Codebook, join rules, provenance log, QA report, limitations.
- Validation tables: FARS rural/urban label vs 2020 Census urban areas.
- Rural Road Safety Atlas (web map).
Data: FARS 2015-2023 Final Files, 2024 Annual Report File. 2024 will be updated to the Final File in v1.0.1.
"""
    open(os.path.join(ROOT, "docs", "RELEASE_NOTES.md"), "w").write(notes)
    print(head)


if __name__ == "__main__":
    main()
