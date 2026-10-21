# Codebook

*Plain-language summary: what every column in every file means and where it comes from. Rules for how values are assigned are in [JOIN_RULES.md](JOIN_RULES.md).*

## File 1: `data/processed/panel_county_year_2015_2024.csv`

One row per county per year: 3,143 counties x 10 years = 31,430 rows. Counts are zero where FARS records no deaths. Within each row, rural + urban + unknown = deaths, and the person-type columns add up to deaths.

| Column | Type | Definition | Source |
|---|---|---|---|
| `fips` | text | 5-digit county FIPS code, 2020 Census county geography | TIGER/Line 2020 |
| `state_fips` | text | 2-digit state FIPS code | TIGER/Line 2020 |
| `state` | text | State postal abbreviation | derived |
| `state_name` | text | State name | derived |
| `county_name` | text | County name with legal/statistical area description | TIGER/Line 2020 NAMELSAD |
| `year` | integer | Crash year (FARS data year) | FARS |
| `crashes` | integer | Fatal crashes assigned to the county (join rule 1) | FARS accident file |
| `deaths` | integer | Deaths (sum of FATALS) in crashes assigned to the county | FARS accident file |
| `crashes_rural` | integer | Fatal crashes whose map point is outside a 2020 Census urban area | FARS + 2020 urban areas |
| `crashes_ru_unknown` | integer | Fatal crashes with no usable map point | FARS |
| `crashes_urban` | integer | Fatal crashes whose map point is inside a 2020 Census urban area | FARS + 2020 urban areas |
| `deaths_rural` | integer | Deaths in crashes outside a 2020 Census urban area (primary rural measure) | FARS person file + 2020 urban areas |
| `deaths_ru_unknown` | integer | Deaths in crashes with no usable map point | FARS |
| `deaths_urban` | integer | Deaths in crashes inside a 2020 Census urban area | FARS person file + 2020 urban areas |
| `deaths_fars_rural` | integer | Deaths in crashes FARS labels rural (RUR_URB = 1); NHTSA's definition | FARS RUR_URB |
| `deaths_fars_ru_unknown` | integer | Deaths in crashes with another RUR_URB code (not in inventory, not reported, unknown) | FARS RUR_URB |
| `deaths_fars_urban` | integer | Deaths in crashes FARS labels urban (RUR_URB = 2) | FARS RUR_URB |
| `deaths_cyclist` | integer | Deaths of bicyclists and other cyclists | FARS person file PER_TYP |
| `deaths_driver` | integer | Deaths of drivers | FARS person file PER_TYP |
| `deaths_nonmotorist_other` | integer | Deaths of other non-motorists (personal conveyances, non-motor devices, unknown) | FARS person file PER_TYP |
| `deaths_occupant_other` | integer | Deaths of other or unknown vehicle occupants | FARS person file PER_TYP |
| `deaths_passenger` | integer | Deaths of passengers | FARS person file PER_TYP |
| `deaths_pedestrian` | integer | Deaths of pedestrians | FARS person file PER_TYP |
| `deaths_rural_cyclist` | integer | Rural deaths (Census map) of bicyclists and other cyclists | FARS person file + 2020 urban areas |
| `deaths_rural_driver` | integer | Rural deaths (Census map) of drivers | FARS person file + 2020 urban areas |
| `deaths_rural_nonmotorist_other` | integer | Rural deaths (Census map) of other non-motorists (personal conveyances, non-motor devices, unknown) | FARS person file + 2020 urban areas |
| `deaths_rural_occupant_other` | integer | Rural deaths (Census map) of other or unknown vehicle occupants | FARS person file + 2020 urban areas |
| `deaths_rural_passenger` | integer | Rural deaths (Census map) of passengers | FARS person file + 2020 urban areas |
| `deaths_rural_pedestrian` | integer | Rural deaths (Census map) of pedestrians | FARS person file + 2020 urban areas |
| `deaths_arterial` | integer | Deaths on other principal and minor arterials (3-4) | FARS FUNC_SYS |
| `deaths_collector` | integer | Deaths on major and minor collectors (5-6) | FARS FUNC_SYS |
| `deaths_interstate_fwy` | integer | Deaths on Interstates and other freeways/expressways (FUNC_SYS 1-2) | FARS FUNC_SYS |
| `deaths_local` | integer | Deaths on local roads (7) | FARS FUNC_SYS |
| `deaths_road_unknown` | integer | Deaths on not in inventory, not reported, or unknown (96-99) | FARS FUNC_SYS |
| `deaths_rural_arterial` | integer | Rural deaths (Census map) on other principal and minor arterials (3-4) | FARS FUNC_SYS + 2020 urban areas |
| `deaths_rural_collector` | integer | Rural deaths (Census map) on major and minor collectors (5-6) | FARS FUNC_SYS + 2020 urban areas |
| `deaths_rural_interstate_fwy` | integer | Rural deaths (Census map) on Interstates and other freeways/expressways (FUNC_SYS 1-2) | FARS FUNC_SYS + 2020 urban areas |
| `deaths_rural_local` | integer | Rural deaths (Census map) on local roads (7) | FARS FUNC_SYS + 2020 urban areas |
| `deaths_rural_road_unknown` | integer | Rural deaths (Census map) on not in inventory, not reported, or unknown (96-99) | FARS FUNC_SYS + 2020 urban areas |
| `deaths_own_county` | integer | Deaths on roads owned by: county highway agency | FARS RD_OWNER |
| `deaths_own_federal_tribal` | integer | Deaths on roads owned by: federal agencies and tribal nations | FARS RD_OWNER |
| `deaths_own_other_public_private` | integer | Deaths on roads owned by: other public instrumentality, private, or railroad | FARS RD_OWNER |
| `deaths_own_owner_unknown` | integer | Deaths on roads owned by: not reported or unknown | FARS RD_OWNER |
| `deaths_own_state` | integer | Deaths on roads owned by: state highway agency or other state agency/toll authority | FARS RD_OWNER |
| `deaths_own_town_city` | integer | Deaths on roads owned by: town, township, city, municipal, or local park/toll | FARS RD_OWNER |
| `n_crashes_no_coords` | integer | Crashes in this county-year with no usable map point | FARS |
| `n_crashes_point_in_other_county` | integer | Crashes coded to this county whose map point falls in another county | FARS + TIGER/Line 2020 |
| `population` | integer | Resident population, July 1 estimate | Census Population Estimates (V2019 for 2015-19, V2024 for 2020-24) |
| `pop_source` | text | Which estimate vintage, or how the value was rebuilt | derived |
| `pop_imputed` | boolean | True when population was rebuilt (CT 2020-24) or split (AK 02063/02066, 2015-19) | derived |
| `pop2020_census` | integer | 2020 Census total population | Census 2020 urban/rural county file |
| `pop2020_rural` | integer | 2020 Census rural population (outside urban areas) | Census 2020 urban/rural county file |
| `pct_rural_2020` | number | Percent of 2020 population living in rural areas | Census 2020 urban/rural county file |
| `death_rate_per100k` | number | deaths / population x 100,000 (one year; unstable for small counties) | derived |
| `land_area_m2` | integer | Land area in square meters | TIGER/Line 2020 ALAND |
| `miles_total_2024` | number | Public road centerline miles, 2024 (join rule 7); same value in every year | FHWA HPMS 2024 |
| `miles_rural_fhwa_2024` | number | Public road miles outside FHWA adjusted urban areas (URBAN_ID 99999) | FHWA HPMS 2024 |
| `miles_arterial_2024` | number | Public road miles, other principal and minor arterials (3-4) | FHWA HPMS 2024 F_SYSTEM |
| `miles_collector_2024` | number | Public road miles, major and minor collectors (5-6) | FHWA HPMS 2024 F_SYSTEM |
| `miles_interstate_fwy_2024` | number | Public road miles, Interstates and other freeways/expressways (FUNC_SYS 1-2) | FHWA HPMS 2024 F_SYSTEM |
| `miles_local_2024` | number | Public road miles, local roads (7) | FHWA HPMS 2024 F_SYSTEM |
| `miles_rural_arterial_2024` | number | Rural (FHWA) public road miles, other principal and minor arterials (3-4) | FHWA HPMS 2024 F_SYSTEM, URBAN_ID |
| `miles_rural_collector_2024` | number | Rural (FHWA) public road miles, major and minor collectors (5-6) | FHWA HPMS 2024 F_SYSTEM, URBAN_ID |
| `miles_rural_interstate_fwy_2024` | number | Rural (FHWA) public road miles, Interstates and other freeways/expressways (FUNC_SYS 1-2) | FHWA HPMS 2024 F_SYSTEM, URBAN_ID |
| `miles_rural_local_2024` | number | Rural (FHWA) public road miles, local roads (7) | FHWA HPMS 2024 F_SYSTEM, URBAN_ID |
| `miles_own_county_2024` | number | Public road miles owned by: county highway agency | FHWA HPMS 2024 OWNERSHIP |
| `miles_own_federal_tribal_2024` | number | Public road miles owned by: federal agencies and tribal nations | FHWA HPMS 2024 OWNERSHIP |
| `miles_own_other_public_private_2024` | number | Public road miles owned by: other public instrumentality, private, or railroad | FHWA HPMS 2024 OWNERSHIP |
| `miles_own_owner_unknown_2024` | number | Public road miles owned by: not reported or unknown | FHWA HPMS 2024 OWNERSHIP |
| `miles_own_state_2024` | number | Public road miles owned by: state highway agency or other state agency/toll authority | FHWA HPMS 2024 OWNERSHIP |
| `miles_own_town_city_2024` | number | Public road miles owned by: town, township, city, municipal, or local park/toll | FHWA HPMS 2024 OWNERSHIP |
| `miles_method` | text | county_code, or county_code_plus_map_overlap where blank county codes were assigned by boundary overlap | derived |
| `miles_quality_state` | text | complete / local_roads_mismatch / check: state map mileage vs FHWA Table HM-20 | derived |

## File 2: `data/processed/crash_crosswalk_2015_2024.csv` (also `.csv.gz`)

One row per fatal crash (358,460 rows). Links each FARS crash to its 2020 county, urban area, place, and county subdivision, with match flags.

| Column | Definition |
|---|---|
| `year` | FARS data year |
| `st_case` | FARS case number (unique within a year) |
| `fatals` | Deaths in the crash |
| `fars_county_code` | State + county code as recorded in FARS |
| `fips` | Panel county after join rule 1 (blank if unassigned) |
| `county_rule` | R1_fars_code, R2_recoded_successor, R3_map_point, R4_unassigned |
| `coord_valid` | True if the crash has a usable map point inside a U.S. county |
| `latitude` | FARS LATITUDE |
| `longitude` | FARS LONGITUD |
| `pt_county_geoid` | 2020 county containing the map point |
| `county_point_agrees` | 1 if map point county = panel county, 0 if not, blank if no map point |
| `ru_census` | rural / urban / unknown by 2020 Census urban areas |
| `ua_uace20` | 2020 urban area code containing the point |
| `ua_name20` | 2020 urban area name |
| `ru_fars` | rural / urban / unknown from FARS RUR_URB |
| `fars_rur_urb` | FARS RUR_URB code |
| `fars_func_sys` | FARS FUNC_SYS code |
| `road_class` | Grouped road class (join rule 5) |
| `fars_rd_owner` | FARS RD_OWNER code |
| `road_owner` | Grouped road owner (join rule 5) |
| `place_geoid` | 2020 Census place GEOID containing the point |
| `place_namelsad` | Place name |
| `place_funcstat` | A = active government (incorporated), S = statistical (CDP), others per Census |
| `place_match` | in_incorporated_place / in_cdp / outside_any_place / no_coords |
| `cousub_geoid` | 2020 county subdivision GEOID containing the point |
| `cousub_namelsad` | County subdivision name |
| `cousub_match` | matched / subdivision_not_defined / no_match / no_coords |

## File 3: `data/processed/panel_county_year_long.csv`

Deaths by county, year, location, road class, road owner, and person type, for any cross-tabulation the wide file does not have.

| Column | Definition |
|---|---|
| `fips` | Panel county |
| `year` | Crash year |
| `location` | rural / urban / unknown (2020 Census map) |
| `road_class` | Grouped road class |
| `road_owner` | Grouped road owner |
| `person_type` | Grouped person type |
| `deaths` | Deaths in this combination (zero combinations are omitted) |

## File 4: `data/processed/review_unusual_changes.csv`

County-years flagged by join rule 8, with the author's review status and note.

## File 5: `data/raw/PROVENANCE.txt`

One line per downloaded source file: access date, file name, size, SHA-256 fingerprint, source URL, and a note. The fingerprint lets anyone confirm they have the identical file.
