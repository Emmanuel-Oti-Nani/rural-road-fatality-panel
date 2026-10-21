#!/usr/bin/env python3
"""
01_fetch.py - Download every raw public input and log where it came from.

PLAIN-LANGUAGE NOTE: This script downloads the free federal files the panel is
built from (FARS crash files, Census boundary maps, Census population tables).
Every file it saves is recorded in data/raw/PROVENANCE.txt with its web address,
size, a fingerprint (SHA-256), and the date. You do not need to open this file;
you only run it (see README).

Re-running is safe: files already present are skipped unless --force is given.
"""
import argparse
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
LOG = os.path.join(RAW, "PROVENANCE.txt")
PROV = os.path.join(ROOT, "code", "provenance.py")

YEARS = list(range(2015, 2025))  # v1.0 covers 2015-2024

# State FIPS codes for the 50 states + DC (FARS covers these; Puerto Rico is excluded)
STATES = ["01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17",
          "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31",
          "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "44", "45", "46",
          "47", "48", "49", "50", "51", "53", "54", "55", "56"]


def sources():
    s = []
    for y in YEARS:
        s.append((f"fars/FARS{y}NationalCSV.zip",
                  f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{y}/National/FARS{y}NationalCSV.zip",
                  "NHTSA FARS national CSV file; listed at https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/"))
    s += [
        ("census/tl_2020_us_county.zip",
         "https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip",
         "TIGER/Line 2020 counties (the fixed county geography of the panel)"),
        ("census/tl_2023_us_uac20.zip",
         "https://www2.census.gov/geo/tiger/TIGER2023/UAC/tl_2023_us_uac20.zip",
         "2020 Census urban areas (criteria of Dec 2022), TIGER/Line 2023 vintage"),
        ("census/2020_UA_COUNTY.xlsx",
         "https://www2.census.gov/geo/docs/reference/ua/2020_UA_COUNTY.xlsx",
         "2020 Census urban/rural population and land area by county"),
        ("census/co-est2019-alldata.csv",
         "https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv",
         "Census Population Estimates, county totals, Vintage 2019 (July 1, 2015-2019)"),
        ("census/co-est2024-alldata.csv",
         "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
         "Census Population Estimates, county totals, Vintage 2024 (July 1, 2020-2024)"),
    ]
    s.append(("census/sub-est2024_9.csv",
              "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024_9.csv",
              "Census Population Estimates Vintage 2024, Connecticut towns; used to rebuild the 8 legacy CT counties for 2020-2024"))
    for y in YEARS:
        s.append((f"fars/FARS{y}_Release_Notes.txt",
                  f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{y}/FARS{y}%20Release%20Notes.txt",
                  "NHTSA release notes: records whether the year is an Annual Report File or Final File"))
    for y in range(2021, 2025):
        s.append((f"acs/acsdt5y{y}-b01003.dat",
                  f"https://www2.census.gov/programs-surveys/acs/summary_file/{y}/table-based-SF/data/5YRData/acsdt5y{y}-b01003.dat",
                  f"ACS {y} 5-year table-based summary file, table B01003 total population"))
    for st in STATES:
        s.append((f"census/place/tl_2020_{st}_place.zip",
                  f"https://www2.census.gov/geo/tiger/TIGER2020/PLACE/tl_2020_{st}_place.zip",
                  "TIGER/Line 2020 places"))
        s.append((f"census/cousub/tl_2020_{st}_cousub.zip",
                  f"https://www2.census.gov/geo/tiger/TIGER2020/COUSUB/tl_2020_{st}_cousub.zip",
                  "TIGER/Line 2020 county subdivisions"))
    return s


def fetch(rel, url, note, force=False):
    dest = os.path.join(RAW, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0 and not force:
        return "skip"
    for attempt in range(4):
        try:
            tmp = dest + ".part"
            urllib.request.urlretrieve(url, tmp)
            os.replace(tmp, dest)
            subprocess.run([sys.executable, PROV, dest, url, "--log", LOG, "--note", note], check=True)
            return "ok"
        except Exception as e:  # network hiccup: wait and retry
            err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"failed {url}: {err}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    for rel, url, note in sources():
        try:
            print(fetch(rel, url, note, a.force), rel, flush=True)
        except RuntimeError as e:
            if "Release_Notes" in rel:  # optional: not every year has a notes file
                print("missing (optional)", rel, flush=True)
            else:
                raise


if __name__ == "__main__":
    main()
