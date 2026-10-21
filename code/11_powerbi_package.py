#!/usr/bin/env python3
"""
11_powerbi_package.py - Export the chart data and a matching theme for Power BI Desktop.

PLAIN-LANGUAGE NOTE: The project's charts are drawn in Python in the Power BI style.
If you want to rebuild them as native Power BI visuals (for a report, a dashboard, or
to publish to the Power BI service), this script writes everything you need into
the powerbi/ folder: one small table per chart and a theme file with the same colors
and font. Steps are in powerbi/README.md.
"""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
T = os.path.join(ROOT, "paper", "validation_tables")
O = os.path.join(ROOT, "powerbi")
os.makedirs(O, exist_ok=True)

w = pd.read_csv(os.path.join(P, "panel_county_year_2015_2024.csv"), dtype={"fips": str, "state_fips": str})

# chart 1: deaths by location and year (long format: Year, Location, Deaths)
g = w.groupby("year")[["deaths_rural", "deaths_urban", "deaths_ru_unknown"]].sum().reset_index()
c1 = g.melt(id_vars="year", var_name="location", value_name="deaths")
c1["location"] = c1.location.map({"deaths_rural": "Rural", "deaths_urban": "Urban", "deaths_ru_unknown": "Unknown"})
c1.to_csv(os.path.join(O, "chart1_deaths_by_location.csv"), index=False)

# chart 2: rural share by definition
by = pd.read_csv(os.path.join(T, "agreement_by_year.csv"))
c2 = pd.concat([pd.DataFrame({"year": by.year, "definition": "2020 Census map (fixed)", "rural_share_pct": by.pct_rural_census}),
                pd.DataFrame({"year": by.year, "definition": "FARS rural/urban label", "rural_share_pct": by.pct_rural_fars})])
c2.to_csv(os.path.join(O, "chart2_rural_share_by_definition.csv"), index=False)

# chart 3: county death rate 2020-2024 (for a filled or shape map; FIPS as text)
r = w[w.year >= 2020].groupby(["fips", "county_name", "state"]).agg(deaths=("deaths", "sum"), person_years=("population", "sum")).reset_index()
r["deaths_per_100k_per_year"] = (r.deaths / r.person_years * 1e5).round(2)
r["location_for_map"] = r.county_name + ", " + r.state
r.to_csv(os.path.join(O, "chart3_county_death_rate_2020_2024.csv"), index=False)

# chart 4: rural deaths by person type
pt = w.groupby("year")[["deaths_rural_driver", "deaths_rural_passenger", "deaths_rural_pedestrian", "deaths_rural_cyclist"]].sum().reset_index()
c4 = pt.melt(id_vars="year", var_name="person_type", value_name="rural_deaths")
c4["person_type"] = c4.person_type.str.replace("deaths_rural_", "").str.capitalize() + "s"
c4.to_csv(os.path.join(O, "chart4_rural_deaths_by_person_type.csv"), index=False)

# the full panel, for anyone building their own report
w.to_csv(os.path.join(O, "panel_county_year_2015_2024.csv"), index=False)

theme = {
    "name": "Rural Road Fatality Panel",
    "dataColors": ["#118DFF", "#E66C37", "#12239E", "#6B007B", "#E044A7", "#744EC2", "#D9B300", "#D64550"],
    "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#118DFF",
    "good": "#1AAB40", "neutral": "#D9B300", "bad": "#D64554",
    "maximum": "#12239E", "center": "#7DBFFF", "minimum": "#DCEEFF",
    "textClasses": {
        "title": {"fontFace": "Segoe UI Semibold", "fontSize": 14, "color": "#252423"},
        "header": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": "#252423"},
        "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": "#605E5C"},
        "callout": {"fontFace": "Segoe UI Light", "fontSize": 32, "color": "#252423"},
    },
    "visualStyles": {"*": {"*": {
        "categoryAxis": [{"gridlineShow": False, "showAxisTitle": False}],
        "valueAxis": [{"gridlineShow": True, "gridlineColor": {"solid": {"color": "#E1DFDD"}}}],
        "legend": [{"show": True, "position": "TopLeft"}],
        "border": [{"show": True, "color": {"solid": {"color": "#E1DFDD"}}, "radius": 4}],
    }}},
}
json.dump(theme, open(os.path.join(O, "rural_road_panel_theme.json"), "w"), indent=2)
print("powerbi package written:", sorted(os.listdir(O)))
