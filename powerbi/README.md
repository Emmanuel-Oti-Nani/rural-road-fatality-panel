# Rebuilding the charts in Power BI Desktop

*Plain-language summary: the charts in this project are drawn in the Power BI look (same colors, font, legends, and gridlines), so you do not need Power BI to use them. If you want native Power BI visuals, for example a live report on the Power BI service, this folder has the data and theme. Time: about 30 minutes the first time.*

Power BI Desktop is free from https://www.microsoft.com/power-bi/desktop (Windows only).

## Files

| File | What it is |
|---|---|
| `rural_road_panel_theme.json` | Colors and fonts that match the project figures |
| `chart1_deaths_by_location.csv` | Year, location (Rural, Urban, Unknown), deaths |
| `chart2_rural_share_by_definition.csv` | Year, definition, rural share (%) |
| `chart3_county_death_rate_2020_2024.csv` | One row per county: FIPS, name, deaths, deaths per 100,000 per year |
| `chart4_rural_deaths_by_person_type.csv` | Year, person type, rural deaths |
| `panel_county_year_2015_2024.csv` | The full panel, for your own visuals |

## Steps

1. **Load the theme.** View > Themes > Browse for themes > choose `rural_road_panel_theme.json`.
2. **Load the data.** Home > Get data > Text/CSV, once per file. Click **Load**. In Model view, set `fips` in the county file to **Text** so leading zeros stay.
3. **Chart 1 (line chart).** Insert a Line chart. X-axis: `year`. Y-axis: `deaths`. Legend: `location`. Filter out `Unknown` in the Filters pane. Turn on Data labels > "Show for this series" > last point only.
4. **Chart 2 (line chart).** Same as chart 1 with `chart2_rural_share_by_definition`: Y-axis `rural_share_pct`, Legend `definition`. Set the Y-axis range to 30 to 60.
5. **Chart 3 (map).** Insert a Filled map (or Shape map). Location: `location_for_map`; set its data category to **County** (Column tools > Data category). Color saturation: `deaths_per_100k_per_year`. The theme's minimum/center/maximum colors give the blue scale. Note: Filled map requires the map visual to be enabled by your organization's administrator.
6. **Chart 4 (small multiples).** Insert a Clustered column chart. X-axis: `year`. Y-axis: `rural_deaths`. Small multiples: `person_type`. Format > Small multiples > Y-axis: "Independent" scales.
7. **Save** as `rural_road_panel.pbix`. To share online, Home > Publish (needs a Power BI account).

Every number in these files comes from `data/processed/panel_county_year_2015_2024.csv` and `paper/validation_tables/`, built by `code/11_powerbi_package.py`.
