# Next steps

*Plain-language summary: what later versions add, so v1.0 is understood as the first release of a maintained dataset.*

| Version | Adds | When |
|---|---|---|
| v1.0 | Panel 2015-2024, codebook, provenance log, crash crosswalk, atlas, validation preprint | After the author's verification |
| v1.0.1 | Replace the 2024 Annual Report File with the 2024 Final File | When NHTSA posts it (expected around April 2027) |
| v1.1 | Add 2025 (Annual Report File) | When NHTSA posts the 2025 file |
| v1.2 (option) | Exposure: vehicle miles traveled by county from HPMS traffic counts, for deaths per 100 million vehicle miles | Author decision |
| v1.2 (option) | USDA Rural-Urban Continuum Codes as a third, county-level rural definition | Author decision |

Each new version gets its own Zenodo DOI under the same concept DOI, so citations to "the panel" always resolve to the latest version and citations to a version stay fixed.

To add a year: add it to `YEARS` in `code/01_fetch.py` and `code/02_build.py`, add the matching Census population estimate file, re-run the scripts in order, review the QA report and the new unusual-change flags, and update the release notes.
