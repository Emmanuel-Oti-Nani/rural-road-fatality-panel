# Your verification checklist

*Plain-language version: before anything goes public under your name, you check it. Every file, row, and number below is real and comes from this build. Total time: about 3 to 4 hours. Split it into sittings; Part 4 can be done a few counties at a time. Tick each box and write what you found on the line.*

*The pre-publication check (`tools/publish_gate.py`) handles the mechanical items. These are yours.*

**What you need open:** the project folder; Excel or Google Sheets; the FARS files, downloaded free from https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/ (open a year, then `National`, then the `FARS20xxNationalCSV.zip` file, unzip it, and open `accident.csv`).

## Part 1: The results rebuild (15 to 30 min)

Pick one:
- [ ] **Option A, ask Claude.** In a new chat with Opus 5.5 or Fable 5, attach the project folder and say: "Re-run this pipeline from scratch following the README, then give me the national deaths by year and the 2024 rural deaths under both definitions." Compare with these numbers. They should match exactly:
  - Deaths by year in the FARS files: 2015: 35,484, 2016: 37,806, 2017: 37,473, 2018: 36,835, 2019: 36,355, 2020: 39,007, 2021: 43,230, 2022: 42,721, 2023: 41,025, 2024: 39,254
  - 2024 rural deaths, Census map: 18,760; FARS label: 16,005
- [ ] **Option B, run it yourself** (needs Python): open a terminal in the project folder, paste the commands from the README "Run it" section one by one. The last lines of `python code/03_qa.py` should show the same numbers as above.

## Part 2: National numbers against NHTSA (15 min)

- [ ] Open NHTSA's report *Traffic Safety Facts 2024 Data: Rural/Urban Traffic Fatalities* (DOT HS 813 828): https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813828 . Find the sentence "Of 39,254 traffic fatalities in 2024, 16,006 (41%) were in rural areas and 22,905 (58%) were in urban areas."
  - Our FARS file total for 2024: **39,254**. Match? ___
  - Our 2024 rural deaths using the FARS label: **16,005** (the difference from 16,006 is deaths in crashes that could not be placed in a county; see `data/processed/qa_report.txt` section 2). OK? ___
- [ ] Open NHTSA's FARS state data page https://www-fars.nhtsa.dot.gov/States/StatesFatalitiesFatalityRates.aspx and check the national total for two other years, say 2019 and 2022. Ours: 2019 **36,355**, 2022 **42,721**. If NHTSA's page shows an older (preliminary) number, note it: FARS files are revised after first release. ___

## Part 3: County rows by hand (45 to 60 min)

For each row: find it in the panel file, then count it in the FARS `accident.csv` for that year. A tip for Excel: use Data > Filter, filter `STATE` and `COUNTY`, and the status bar shows the count and the sum of `FATALS` when you select that column.

FARS uses numeric codes: the state code is the first two digits of the county FIPS code without the leading zero, and the county code is the last three digits without leading zeros (Greene County, MO is FIPS 29077, so STATE = 29 and COUNTY = 77).

**Counties you know personally:**
- [ ] **Greene County, MO (2024)** - your home county. In `data/processed/panel_county_year_2015_2024.csv`, row 15,231: `deaths` = **38**, `crashes` = **37**, `deaths_rural` = 10, `deaths_pedestrian` = 5. Check: open `accident.csv` from the FARS 2024 file, filter `STATE` = 29 and `COUNTY` = 77. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Greene County, MO (2015)** - your home county, first year. In `data/processed/panel_county_year_2015_2024.csv`, row 15,222: `deaths` = **28**, `crashes` = **27**, `deaths_rural` = 4, `deaths_pedestrian` = 5. Check: open `accident.csv` from the FARS 2015 file, filter `STATE` = 29 and `COUNTY` = 77. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Laclede County, MO (2024)** - a rural Ozarks county you know. In `data/processed/panel_county_year_2015_2024.csv`, row 15,371: `deaths` = **10**, `crashes` = **9**, `deaths_rural` = 8, `deaths_pedestrian` = 0. Check: open `accident.csv` from the FARS 2024 file, filter `STATE` = 29 and `COUNTY` = 105. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Christian County, MO (2024)** - Christian County, next to Springfield. In `data/processed/panel_county_year_2015_2024.csv`, row 15,061: `deaths` = **5**, `crashes` = **5**, `deaths_rural` = 4, `deaths_pedestrian` = 0. Check: open `accident.csv` from the FARS 2024 file, filter `STATE` = 29 and `COUNTY` = 43. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Taney County, MO (2024)** - Taney County, Branson tourism traffic. In `data/processed/panel_county_year_2015_2024.csv`, row 15,901: `deaths` = **13**, `crashes` = **13**, `deaths_rural` = 7, `deaths_pedestrian` = 0. Check: open `accident.csv` from the FARS 2024 file, filter `STATE` = 29 and `COUNTY` = 213. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___

**Hard cases (the join rules at work):**
- [ ] **Oglala Lakota County, SD (2022)** - FARS still uses the old Shannon County code; tests rule R2. In `data/processed/panel_county_year_2015_2024.csv`, row 24,139: `deaths` = **10**, `crashes` = **8**, `deaths_rural` = 10, `deaths_pedestrian` = 2. Check: open `accident.csv` from the FARS 2022 file, filter `STATE` = 46 and `COUNTY` = 102 (also COUNTY = 113, the old Shannon County code). Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Fairfield County, CT (2024)** - Connecticut legacy county; tests the town-sum population. In `data/processed/panel_county_year_2015_2024.csv`, row 3,101: `deaths` = **57**, `crashes` = **50**, `deaths_rural` = 4, `deaths_pedestrian` = 13. Check: open `accident.csv` from the FARS 2024 file, filter `STATE` = 9 and `COUNTY` = 1. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Copper River Census Area, AK (2016)** - Copper River, Alaska: split from Valdez-Cordova in 2019, so its 2016 crashes are placed by map point (rule R3). In `data/processed/panel_county_year_2015_2024.csv`, row 733: `deaths` = **3**, `crashes` = **3**, `deaths_rural` = 3, `deaths_pedestrian` = 1. Check: open `accident.csv` from the FARS 2016 file, filter `STATE` = 2 and `COUNTY` = 66 (also COUNTY = 261, Valdez-Cordova, whose crashes are placed by map point). Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___

**Extreme values:**
- [ ] **Los Angeles County, CA (2024)** - the most deaths of any county in 2024. In `data/processed/panel_county_year_2015_2024.csv`, row 2,061: `deaths` = **778**, `crashes` = **726**, `deaths_rural` = 85, `deaths_pedestrian` = 316. Check: open `accident.csv` from the FARS 2024 file, filter `STATE` = 6 and `COUNTY` = 37. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **La Paz County, AZ (2024)** - the highest 2024 death rate among counties of 10,000+ people. In `data/processed/panel_county_year_2015_2024.csv`, row 1,041: `deaths` = **29**, `crashes` = **20**, `deaths_rural` = 23, `deaths_pedestrian` = 3. Check: open `accident.csv` from the FARS 2024 file, filter `STATE` = 4 and `COUNTY` = 12. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___

**Random rows:**
- [ ] **Edwards County, IL (2015)** - random row (seed 20261021). In `data/processed/panel_county_year_2015_2024.csv`, row 6,192: `deaths` = **3**, `crashes` = **2**, `deaths_rural` = 3, `deaths_pedestrian` = 0. Check: open `accident.csv` from the FARS 2015 file, filter `STATE` = 17 and `COUNTY` = 47. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Runnels County, TX (2021)** - random row (seed 20261021). In `data/processed/panel_county_year_2015_2024.csv`, row 27,238: `deaths` = **6**, `crashes` = **4**, `deaths_rural` = 6, `deaths_pedestrian` = 0. Check: open `accident.csv` from the FARS 2021 file, filter `STATE` = 48 and `COUNTY` = 399. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Peoria County, IL (2019)** - random row (seed 20261021). In `data/processed/panel_county_year_2015_2024.csv`, row 6,676: `deaths` = **11**, `crashes` = **10**, `deaths_rural` = 3, `deaths_pedestrian` = 3. Check: open `accident.csv` from the FARS 2019 file, filter `STATE` = 17 and `COUNTY` = 143. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Cass County, MN (2017)** - random row (seed 20261021). In `data/processed/panel_county_year_2015_2024.csv`, row 13,254: `deaths` = **6**, `crashes` = **6**, `deaths_rural` = 6, `deaths_pedestrian` = 0. Check: open `accident.csv` from the FARS 2017 file, filter `STATE` = 27 and `COUNTY` = 21. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___
- [ ] **Pope County, IL (2019)** - random row (seed 20261021). In `data/processed/panel_county_year_2015_2024.csv`, row 6,716: `deaths` = **1**, `crashes` = **1**, `deaths_rural` = 1, `deaths_pedestrian` = 0. Check: open `accident.csv` from the FARS 2019 file, filter `STATE` = 17 and `COUNTY` = 151. Count the rows (crashes) and add up `FATALS` (deaths). Mine: ___

If a count differs by one or two, check `n_crashes_point_in_other_county` and `county_rule` in `data/processed/crash_crosswalk_2015_2024.csv` (filter by `fips`) before calling it an error, and write it down. Claude will trace any difference you find.

## Part 4: Counties with unusual changes (60 to 90 min; can be spread over several days)

Your stated role includes reviewing every county with an unusual change between years. The build flagged **206 county-years in 193 counties** (`data/processed/review_unusual_changes.csv`). For each, decide: **OK** (a real change, for example one multi-death crash, a new highway segment, a known event) or **FIX** (looks like a coding error). Write OK or FIX in `review_status` and a few words in `review_note`.

The file already helps: `crashes` is the number of fatal crashes that year, `largest_crash_deaths` is the deadliest single crash, and `hint` marks the rows where one multi-death crash explains much of the jump (usually OK after a quick look). `expected` is what the county's other years predict, adjusted for the national level that year. For the rest, filter the crosswalk file to that `fips` and `year`, filter the crosswalk file to that `fips` and `year` look at the crashes (road class, map point), and decide. A local news search for the county and year often settles it. The eight strongest flags:

| County | Year | Deaths | Year before | Expected | Largest single crash |
|---|---|---|---|---|---|
| Bradley County, AR (05011) | 2020 | 13 | 2 | 1.6 | 3 |
| Cheyenne County, CO (08017) | 2020 | 10 | 0 | 1.1 | 8 |
| Cook County, IL (17031) | 2021 | 458 | 371 | 353.9 | 4 |
| Liberty County, GA (13179) | 2020 | 32 | 8 | 9.0 | 6 |
| Decatur County, IN (18031) | 2016 | 17 | 0 | 3.5 | 2 |
| Schoharie County, NY (36095) | 2018 | 28 | 2 | 3.0 | 20 |
| Vilas County, WI (55125) | 2016 | 14 | 4 | 2.6 | 3 |
| Armstrong County, TX (48011) | 2022 | 12 | 3 | 1.8 | 5 |

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
- [ ] **Road miles where local roads are incomplete.** In 11 of 51 states the HPMS map mileage is more than 5 percent away from FHWA's official state total (AK, AZ, DC, ID, KY, NJ, OR, UT, WA, WI, WY), almost always because local roads are missing from the map data.
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
