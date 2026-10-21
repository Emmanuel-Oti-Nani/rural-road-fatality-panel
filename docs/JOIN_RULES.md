# Join rules

*Plain-language summary: these are the rules the build follows to place each fatal crash in a county, label it rural or urban, find its town or city, and sort the people who died. Emmanuel Oti Nani designed and approves these rules; any change is recorded here first, then in the code (`code/02_build.py`).*

## The unit

One row of the panel = one county in one year. The county list is fixed: the 3,143 counties and county-equivalents of the 50 states and the District of Columbia in the 2020 Census (TIGER/Line 2020). Using one fixed county map means 2015 and 2024 are counted on the same geography.

## Rule 1: Which county a crash belongs to

Applied in order. The rule used for each crash is stored in the crosswalk column `county_rule`.

| Rule | When it applies | What happens |
|---|---|---|
| R1 `fars_code` | The FARS state and county code is a 2020 county | Use that county |
| R2 `recoded_successor` | The code is an old county with one successor | Recode: Shannon County, SD (46113) to Oglala Lakota County (46102); Wade Hampton Census Area, AK (02270) to Kusilvak Census Area (02158) |
| R3 `map_point` | The code is not a 2020 county (for example Valdez-Cordova, AK, 02261, which split in 2019) or is unknown (997, 998, 999), and the crash has a usable map point | Use the 2020 county the map point falls in |
| R4 `unassigned` | No usable code and no usable map point | The crash is not placed in any county; it is counted in the QA report |

Why the FARS code comes first: it is the county the investigating agency recorded and NHTSA quality-checked. Map points can sit a few meters off near county lines. Where the map point falls in a different county than the code, the crash keeps its coded county and the panel counts it in `n_crashes_point_in_other_county` so you can see how often this happens.

Connecticut: FARS keeps coding Connecticut's eight legacy counties in every year through 2024, even though the Census Bureau replaced them with nine planning regions in 2022. The panel keeps the eight legacy counties.

## Rule 2: Rural or urban

- **Primary (`ru_census`)**: the crash is **urban** if its map point falls inside a 2020 Census urban area, **rural** if it falls outside, and **unknown** if it has no usable map point. The same 2020 map is used for every year.
- **Comparison (`ru_fars`)**: the FARS variable RUR_URB (1 = rural, 2 = urban, other codes = unknown). This label follows the Federal Highway Administration's adjusted urban boundaries in force when the crash was coded. It is the definition NHTSA uses in its own rural/urban reports.
- A usable map point: LATITUDE between 17 and 72 and LONGITUD between -180 and -64 (this excludes FARS missing-value codes such as 77.7777, 88.8888, 99.9999), and the point falls inside a U.S. county.

## Rule 3: Town or city, and county subdivision (the crosswalk)

- **Place**: the 2020 Census place (incorporated city, town, or village, or a census-designated place, CDP) that contains the map point. `place_match` says `in_incorporated_place`, `in_cdp`, `outside_any_place`, or `no_coords`.
- **County subdivision**: the 2020 county subdivision (township, town, or census county division) that contains the map point. `cousub_match` says `matched`, `subdivision_not_defined` (Census code 00000), `no_match`, or `no_coords`.
- A point exactly on a shared boundary takes the first match.

## Rule 4: Who died

Deaths are people in the FARS person file with INJ_SEV = 4 (fatal injury, death within 30 days). Each year, these match the FATALS total in the crash file exactly (see the QA report).

| Panel group | FARS PER_TYP codes |
|---|---|
| driver | 1 Driver of a motor vehicle in transport |
| passenger | 2 Passenger of a motor vehicle in transport |
| occupant_other | 3 Occupant of a motor vehicle not in transport; 9 Unknown occupant type |
| pedestrian | 5 Pedestrian |
| cyclist | 6 Bicyclist; 7 Other cyclist |
| nonmotorist_other | 4 Occupant of a non-motor vehicle transport device; 8 Person on a personal conveyance; 10 Person in or on a building; 19 Unknown non-motorist type |

## Rule 5: Road type and road owner

- **Road class** from FARS FUNC_SYS: `interstate_fwy` (1 Interstate, 2 Other freeway or expressway), `arterial` (3 Other principal arterial, 4 Minor arterial), `collector` (5 Major collector, 6 Minor collector), `local` (7), `road_unknown` (96 Not in state inventory, 97 Not reported, 98, 99 Unknown).
- **Road owner** from FARS RD_OWNER, grouped the same way for crashes and for HPMS road miles: `state` (1, 11, 21, 31), `county` (2), `town_city` (3, 4, 12, 25, 32), `federal_tribal` (50, 60 to 80, 62), `other_public_private` (26, 27, 40), `owner_unknown` (all other codes).

## Rule 6: Population

- **2015 to 2019**: Census Population Estimates, Vintage 2019, July 1 estimates.
- **2020 to 2024**: Census Population Estimates, Vintage 2024, July 1 estimates.
- **Connecticut 2020 to 2024**: the Census publishes planning regions only, so the eight legacy counties are rebuilt by adding up town (county subdivision) estimates; each town belongs to exactly one legacy county.
- **Alaska 2015 to 2019**: Valdez-Cordova was split into Chugach (02063) and Copper River (02066) using each part's share of the 2020 Census population.
- Rebuilt or split values carry `pop_imputed = True`.
- **Rural population** is from the 2020 Census only (`pop2020_rural`), because the Census does not estimate rural population each year.

## Rule 7: Road miles (FHWA HPMS, 2024, one snapshot)

- Source: the full HPMS 2024 map layers on FHWA's map server (geo.dot.gov), one per state.
- Count a road section when it has a functional class (F_SYSTEM 1 to 7) and is mainline (FACILITY_TYPE 1 one-way or 2 two-way). Local roads with a blank FACILITY_TYPE also count. This leaves out ramps, the second direction of divided highways, and planned roads, which is how FHWA counts public road length.
- Rural miles: sections with URBAN_ID = 99999 (outside FHWA adjusted urban areas). Note this is FHWA's rural, not the Census map used for deaths.
- Sections with a blank county code (mostly California) are assigned by the 2020 county boundary they touch; a section crossing a county line counts in both (`miles_method = county_code_plus_map_overlap`).
- Each state's map total is compared with FHWA's official Table HM-20. `miles_quality_state` is `complete` when within 5 percent, `local_roads_mismatch` when arterials and collectors are within 5 percent but the total is not (local roads missing from the map data, or in a few states counted differently), and `check` otherwise. Use local and total miles only where the flag says `complete`.

## Rule 8: Unusual year-to-year changes

A county-year is flagged for the author's review when its deaths fall outside what chance would produce 999 times in 1,000, given the county's average in the other nine years (Poisson test), and it differs from the previous year by 5 or more deaths. Flagged rows are in `data/processed/review_unusual_changes.csv`, where Emmanuel records OK (a real change) or FIX for each.
