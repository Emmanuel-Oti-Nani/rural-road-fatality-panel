# Publish guide

*Plain-language summary: how to put this project online under your name, step by step. Do these only after you finish `docs/VERIFY_CHECKLIST.md` and tell Claude you approve. Total time: about 1 to 1.5 hours across four parts. Nothing here costs money.*

| Part | What you get | Who does it | Time |
|---|---|---|---|
| 1. GitHub | Public project page and code | Claude (with a token from you) or you | 10 to 20 min |
| 2. Zenodo, panel | Permanent DOI for the panel v1.0 | Automatic from a GitHub release | 10 min |
| 3. Zenodo, crosswalk | A second DOI for the crosswalk | You, by upload | 15 min |
| 4. Atlas | Live web map on GitHub Pages | You, one setting | 5 min |
| 5. engrXiv | Validation study preprint | You (it is an attestation) | 30 min plus your rewrite |

## Copy-ready text

**Repository name:** `rural-road-fatality-panel`

**Repository description:** Open county-by-year panel of U.S. road deaths, 2015-2024, split by rural and urban location, road type, and person type, with a web atlas. Built from NHTSA FARS and the 2020 Census.

**Release title:** `v1.0.0 - U.S. Rural Road Fatality County Panel, 2015-2024`

**Release notes:** paste the contents of `docs/RELEASE_NOTES.md`.

**Author:** Emmanuel Oti Nani, Independent Researcher, Springfield, Missouri, USA, ORCID 0009-0009-4175-8962

**Keywords:** traffic safety; rural roads; FARS; county panel; road fatalities; urban areas; open data; transportation

## Part 1: GitHub (10 to 20 min)

**Option A (easiest): let Claude push it.**
1. Go to https://github.com/settings/personal-access-tokens/new (log in first).
2. Token name: `rural-panel-upload`. Expiration: 7 days.
3. Repository access: "All repositories" (the repository does not exist yet, so it cannot be selected).
4. Permissions, Repository permissions: set **Administration** to "Read and write" (to create the repository) and **Contents** to "Read and write". Leave everything else as is.
5. Click **Generate token**. Copy the token (it starts with `github_pat_`). You only see it once.
6. Paste it to Claude in the chat with: "Here is my GitHub token for the upload." Claude stores it only for this session, never in a file.
7. After Claude confirms the push, delete the token: https://github.com/settings/personal-access-tokens, click the token, **Delete**.

**Option B: do it yourself with GitHub Desktop** (no typing commands).
1. Install GitHub Desktop: https://desktop.github.com and sign in.
2. File > Add local repository > choose the project folder > "create a repository" if asked. Name: `rural-road-fatality-panel`.
3. Click **Publish repository**. Untick "Keep this code private". Click **Publish**.
4. The screen should show "Last fetched just now." Your page is https://github.com/Emmanuel-Oti-Nani/rural-road-fatality-panel

## Part 2: Zenodo DOI for the panel (10 min)

Do Part 2 before making a GitHub release, so the release triggers the DOI.

1. Log in at https://zenodo.org with **Log in with ORCID** (this links your ORCID automatically).
2. Click your name (top right) > **GitHub** > **Connect** and approve.
3. In the list of repositories, find `rural-road-fatality-panel` and flip the switch to **On**. (Click **Sync now** if it is missing.)
4. On GitHub, open your repository > **Releases** (right side) > **Create a new release**.
5. **Choose a tag** > type `v1.0.0` > "Create new tag". Title and notes from "Copy-ready text" above. Click **Publish release**.
6. Wait 2 to 5 minutes. On Zenodo, click your name > **GitHub**. The repository now shows a blue DOI badge. Click it. The DOI looks like `10.5281/zenodo.1234567`.
7. Zenodo reads the title, author, and description from the `.zenodo.json` file in the project, so they match exactly.
8. Send Claude the DOI. Claude puts it into `README.md`, `CITATION.cff`, the atlas footer, and the manuscript, and pushes the update.

## Part 3: Zenodo DOI for the crosswalk (15 min)

The crosswalk gets its own record so others can cite it on its own.

1. Claude prepares `release/crosswalk_v1.0.0.zip` (the crosswalk CSV, `docs/JOIN_RULES.md`, the crosswalk part of the codebook, and `LICENSE`).
2. On Zenodo, click **New upload**.
3. Drag in the zip file.
4. Fill in from `docs/zenodo_crosswalk_metadata.json` (Claude can paste each field to you):
   - Resource type: **Dataset**
   - Title: `FARS Fatal Crash to 2020 Census Place and County Subdivision Crosswalk, 2015-2024`
   - Creators: Nani, Emmanuel Oti; ORCID 0009-0009-4175-8962; affiliation Independent Researcher, Springfield, Missouri, USA
   - Description: copy from the metadata file
   - License: **Creative Commons Attribution 4.0 International**
   - Version: `1.0.0`
   - Related works: "Is supplement to" the panel DOI from Part 2
5. Click **Publish**. Confirm. Copy the new DOI and send it to Claude.

## Part 4: Turn on the atlas (5 min)

1. On GitHub, open the repository > **Settings** > **Pages** (left menu).
2. Under "Build and deployment", Source: choose **GitHub Actions**.
3. Click the **Actions** tab. Open "Publish atlas" and click **Run workflow** if it has not already run.
4. After about 2 minutes, the atlas is live at https://emmanuel-oti-nani.github.io/rural-road-fatality-panel/
5. Open it. The red DRAFT bar should be gone (Claude removes it in the final build). Click Greene County, MO and check the numbers match your checklist.

## Part 5: engrXiv preprint (30 min, plus your rewrite)

**Important, read first.** engrXiv's AI policy (https://engrxiv.org/ai-policy) does **not** allow submitting AI-generated text verbatim, including whole paragraphs. `paper/preprint/main.pdf` (built from `main.tex`) has verified tables, figures, and numbers, but the prose was drafted by Claude. Before you submit, **rewrite every paragraph in your own words** (edit `code/preprint_template.tex`, then run `python code/10_preprint_tex.py`, or ask Claude to rebuild it). Claude can help you line by line and check that every number still matches `paper/stats.json`, but the sentences must be yours. Then update the "Use of AI tools" statement so it describes exactly how you used Claude (for example: code, data assembly, and a structured first draft that the author rewrote).

1. Log in at https://engrxiv.org (you already have an account).
2. Click **Submit** (or "Submit a preprint").
3. Tick each item of the Submission Preparation Checklist. Read the AI policy and confirm.
4. Do Parts 1 and 2 first, so the dataset DOI exists. Ask Claude to rebuild the preprint with the DOI (`python code/10_preprint_tex.py --doi 10.5281/zenodo.NNNNNNN`). Upload `paper/preprint/main.pdf`.
5. Title: copy from the manuscript. Abstract: copy your rewritten abstract.
6. Authors: Emmanuel Oti Nani, ORCID 0009-0009-4175-8962, Independent Researcher, Springfield, Missouri, USA, otiemmanuelnani@gmail.com.
7. Keywords: rural; traffic fatalities; FARS; urban areas; measurement validity; road safety; open data.
8. Add the data DOI from Part 2 where the form asks for supplementary material or data links.
9. Submit. Posting is permanent and cannot be withdrawn, so check the PDF one last time.
10. When it is posted, send Claude the engrXiv link and DOI.

## After each step: log it the same day

Add a row to your evidence log (your Exhibits folder) for each item:

```
date,artifact_or_event,type,venue_or_host,link_or_doi,status,prong_tags,metrics_snapshot,files_saved,notes
YYYY-MM-DD,U.S. Rural Road Fatality County Panel v1.0.0,dataset,Zenodo + GitHub,10.5281/zenodo.NNNNNNN,live,,0 downloads at release,zenodo_record.pdf; github_release.pdf,Released after author verification
```

Save a PDF of each live page (in your browser: Print > Save as PDF). Publications that are not logged the day they happen are the ones that go missing later.
