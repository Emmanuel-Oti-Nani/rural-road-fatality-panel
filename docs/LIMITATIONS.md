# Limitations

*Plain-language summary: what this panel can and cannot tell you. Read this before using or citing the data.*

1. **2024 is preliminary.** FARS 2024 is NHTSA's Annual Report File (first released April 1, 2026). NHTSA replaces it with a Final File about a year later. County numbers for 2024 can change slightly. Versions 2015 to 2023 are Final Files.
2. **Rural by one fixed map.** "Rural" means outside a 2020 Census urban area, applied to all ten years. A place that grew into an urban area during the decade is treated as urban for all years, and the reverse. This keeps years comparable, but it is not the definition NHTSA uses, so national rural totals differ from NHTSA's published rural totals. Both are in the panel.
3. **Missing map points.** About 0.4 percent of crashes have no usable map point. They are counted in their county but labeled `unknown` for rural or urban and have no town or city match.
4. **Small numbers.** Most counties record few deaths per year. A single crash can double a small county's count. Single-year rates in small counties are mostly noise; use multi-year totals.
5. **Where the crash happened, not where people live.** A county's deaths include travelers who live elsewhere. Rates per resident are a standard measure but do not describe the risk to residents alone. Highway corridors through small counties raise their rates.
6. **Population denominators.** Annual population comes from Census estimates, which carry error, especially for very small counties. Rural population is from the 2020 Census only. Connecticut 2020 to 2024 and Alaska's Chugach and Copper River 2015 to 2019 populations are rebuilt, not published directly.
7. **Road miles are uneven by state.** The FHWA HPMS map layers do not include every local road in every state. Mileage is a 2024 snapshot applied to all years. Use the `miles_quality_state` flag. California's blank county codes were assigned by map overlap, which slightly overcounts miles near county lines.
8. **Road type and owner come from FARS coding.** They describe the road where the crash happened, as coded by state FARS analysts, with some "not reported" and "unknown" values.
9. **Fatal crashes only.** FARS covers crashes with a death within 30 days on a public road. Serious injuries, which are far more numerous, are not included.
10. **Puerto Rico is not included.** FARS covers the 50 states and the District of Columbia.
