# Start Here: U.S. Rural Road Fatality County Panel and Atlas

*Read this first. It explains your project in plain language. Words in bold are explained in [GLOSSARY.md](GLOSSARY.md).*

## What you are building

A free, downloadable table that counts road deaths in every U.S. county for every year from 2015 to 2024, split into rural and urban, by type of road, and by who died (driver, passenger, person walking, person on a bicycle), plus a public map of it.

## Why it matters

In 2024, 39,254 people died on U.S. roads. The National Highway Traffic Safety Administration (NHTSA) reports that 41 percent of them died in rural areas, where only about 21 percent of Americans live. Small rural counties rarely have staff to pull these numbers together, so they apply for federal safety grants without county-level evidence. Today no open table shows rural deaths and the roads they happen on, county by county, across a full decade. This project fills that gap.

Think of it like a county report card for road safety, built the same way for every county so they can be compared fairly.

## Where the information comes from

All sources are free and public. Nothing here needs special permission.

| Source | In plain terms | What one row looks like | Link |
|---|---|---|---|
| **FARS** (Fatality Analysis Reporting System) | NHTSA's record of every fatal crash on a U.S. public road | One crash: date, county, map location, road type; and one row per person involved | https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars |
| 2020 Census **urban areas** | The Census Bureau's official map of what counts as urban; everything outside is rural | One urban area: name and its boundary on the map | https://www.census.gov/programs-surveys/geography/guidance/geo-areas/urban-rural.html |
| Census county, place, and county subdivision maps | Official boundaries of counties, towns and cities, and townships | One county or town and its boundary | https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html |
| Census population (estimates and the **American Community Survey**) | How many people live in each county each year | One county: population for a year | https://www.census.gov/programs-surveys/popest.html |
| **HPMS** (Highway Performance Monitoring System) | The Federal Highway Administration's map of public roads, with type and owner | One stretch of road: length, road class, who owns it | https://www.fhwa.dot.gov/policyinformation/hpms.cfm |

## What you will have at the end

- [x] **A public project page** on GitHub where anyone can see and reuse your work: https://github.com/Emmanuel-Oti-Nani/rural-road-fatality-panel
- [x] **Panel v1.0** with a permanent citation number (**DOI**) from Zenodo: https://doi.org/10.5281/zenodo.23547650
- [x] **Codebook and provenance log**: what every column means and exactly where every file came from
- [ ] **Crosswalk** linking every fatal crash to its 2020 Census town or city and county subdivision, with its own DOI
- [x] **Rural Road Safety Atlas**: a public web map with county views and downloadable figures: https://emmanuel-oti-nani.github.io/rural-road-fatality-panel/
- [x] **Validation study** (a short paper for a **preprint** server): how often FARS's own "rural" label agrees with the Census map: https://doi.org/10.31223/X5RV4C

## How it connects to your work

Your research looks at how communities plan public infrastructure, from Springfield, Missouri, a city surrounded by rural counties. This panel gives every small county the same road-safety evidence a large city can afford to build.

## What you need to do

| Your task | When | Time |
|---|---|---|
| Accounts (ORCID, GitHub, Zenodo, Claude): you already have these | Done | 0 min |
| Answer four setup questions | Now | 10 min |
| Check the results using the checklist | When the draft is ready | 1 to 2 hours |
| Approve publishing | After checking | 5 min |
| Post the validation preprint yourself, using the guide | After publishing | 20 min |

Everything else is built for you.

## The steps ahead

1. **Data collected.** We download the public sources and record exactly where each came from.
2. **Data combined.** Each crash is placed in its county and marked rural or urban, then counted.
3. **Quality checks.** National totals are compared with NHTSA's published numbers, and counties with unusual jumps are flagged for you.
4. **Validation study.** FARS's rural label is compared with the Census map.
5. **Figures and atlas.** You see the first charts and the draft web map.
6. **Ready for your check.** You verify, then we publish.

*You are here: step 6, ready for your check. Open docs/VERIFY_CHECKLIST.md next.*
