# Talking about the U.S. Rural Road Fatality County Panel

*Every number below comes from `paper/stats.json`. Re-run `python code/07_docs.py` after any data change.*

## 60-second version

**The problem.** In 2024, 39,254 people died on U.S. roads. NHTSA reports that 41 percent died in rural areas, where about one in five Americans lives. But small rural counties rarely have staff to build their own road-safety evidence, and there was no open table showing rural deaths, county by county, across a full decade.

**What I built.** An open county-by-year panel of every fatal crash from 2015 to 2024: 389,190 deaths in 3,143 counties, split rural and urban, by road type, road owner, and who died, with population and road miles. Every crash is also linked to its town or city. It comes with a public web map, the Rural Road Safety Atlas.

**What it shows.** How you define "rural" changes the answer. Using one fixed 2020 Census map, 47.8 percent of 2024 deaths were rural, compared with 40.8 percent under the label in the federal crash file. And the rural count looks roughly flat over the decade on the fixed map (18,325 in 2015, 18,760 in 2024), while the federal label shows a decline (17,715 to 16,005).

**Who can use it.** County engineers and planners, state highway safety offices, regional planning commissions, grant writers for federal Safe Streets and Roads for All funding, and researchers.

**Where it is.** GitHub: https://github.com/Emmanuel-Oti-Nani/rural-road-fatality-panel. Zenodo DOI: pending (assigned at the first Zenodo release). Atlas: https://emmanuel-oti-nani.github.io/rural-road-fatality-panel/.

## Two-sentence version

I built and maintain the U.S. Rural Road Fatality County Panel, an open county-by-year dataset of every U.S. road death from 2015 to 2024, split by rural and urban location, road type, and who died, with a public web atlas. It shows that the federal crash file's rural label counts fewer rural deaths than the Census map does (40.8 versus 47.8 percent in 2024), which matters for how rural safety funding is targeted.

## Questions you may be asked

1. **Where does the data come from?** From NHTSA's Fatality Analysis Reporting System, the federal census of every fatal crash on public roads, joined to Census Bureau maps and population and to FHWA road data. All are free public sources; every file is logged with its web address and a digital fingerprint.
2. **What are its limits?** 2024 is NHTSA's preliminary file. "Rural" uses one fixed 2020 map for every year. Small counties have few deaths, so single-year rates jump around. Road miles are incomplete for local roads in some states. Deaths are counted where the crash happened, not where people lived.
3. **Why does this matter for the United States?** Rural roads carry a far larger share of deaths than of population. Federal safety programs ask counties for local evidence. This panel gives every county, including the smallest, the same decade of evidence, free and in the same format.
