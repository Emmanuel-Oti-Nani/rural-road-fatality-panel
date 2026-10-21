#!/usr/bin/env python3
"""
01b_fetch_hpms.py - Download 2024 public road mileage by county, road class, and owner.

PLAIN-LANGUAGE NOTE: The Federal Highway Administration (FHWA) keeps a map of
every public road (HPMS). Instead of downloading millions of road pieces, this
script asks FHWA's map server to add up the miles for us, county by county,
by road class and by owner, and saves the answer. It asks twice: once for all
roads and once for roads outside urban areas (FHWA's "rural" roads).
You do not need to open this file.

Mileage rule (decided in the build spec): count a road piece when it has a
functional class (F_SYSTEM 1-7) and is a mainline road (FACILITY_TYPE 1 = one-way
or 2 = two-way). This excludes ramps, non-inventory directions of divided highways,
and planned roads, which matches how FHWA counts public road length (checked:
Missouri rural arterial and collector miles match FHWA Table HM-20 exactly).
Some states leave FACILITY_TYPE blank on local roads, so local roads (F_SYSTEM 7)
with a blank FACILITY_TYPE are also counted.

Some states (notably California) leave the county code blank on many road pieces.
For those pieces a second pass asks the server to add up the miles that touch each
2020 county boundary. A road piece that crosses a county line is counted in both
counties, so these counties carry a small overcount; they are flagged.
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "raw", "hpms")
LOG = os.path.join(ROOT, "data", "raw", "PROVENANCE.txt")
PROV = os.path.join(ROOT, "code", "provenance.py")
YEAR = 2024
BASE = "https://geo.dot.gov/server/rest/services/Hosted/HPMS_FULL_{st}_{y}/FeatureServer/0/query"
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN",
          "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
          "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
          "VT", "VA", "WA", "WV", "WI", "WY"]
WHERE = {
    "all": "f_system IS NOT NULL AND (facility_type IN (1,2) OR (f_system = 7 AND facility_type IS NULL))",
    "rural": "f_system IS NOT NULL AND (facility_type IN (1,2) OR (f_system = 7 AND facility_type IS NULL)) AND urban_id = 99999",
}
STATS = json.dumps([{"statisticType": "sum", "onStatisticField": "sectionlength", "outStatisticFieldName": "miles"},
                    {"statisticType": "count", "onStatisticField": "objectid", "outStatisticFieldName": "n_sections"}])


def get(url, params, tries=5):
    full = url + "?" + urllib.parse.urlencode(params)
    err = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(full, timeout=180) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d, full
        except Exception as e:
            err = e
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"{full}: {err}")


def post(url, params):
    data = urllib.parse.urlencode(params).encode()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=180) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception as e:
            err = e
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"{url}: {err}")


def spatial_pass(st, url, fips_state):
    """Assign miles with a blank county code to 2020 counties by map overlap."""
    import geopandas as gpd
    cty = gpd.read_file(os.path.join(ROOT, "data", "raw", "census", "tl_2020_us_county.zip"))
    cty = cty[cty.STATEFP == fips_state].to_crs(4326)
    out = {"all": [], "rural": []}
    for _, c in cty.iterrows():
        geom = c.geometry.simplify(0.002)
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        rings = []
        for p in polys:
            rings.append([list(xy) for xy in p.exterior.coords])
            rings += [[list(xy) for xy in i.coords] for i in p.interiors]
        g = json.dumps({"rings": rings, "spatialReference": {"wkid": 4326}})
        for key, where in WHERE.items():
            d = post(url, {"where": where + " AND county_id IS NULL", "geometry": g, "geometryType": "esriGeometryPolygon",
                           "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                           "groupByFieldsForStatistics": "f_system,ownership", "outStatistics": STATS, "f": "json"})
            for f in d.get("features", []):
                out[key].append({**f["attributes"], "county_id": int(c.COUNTYFP)})
        print("    county", c.GEOID, flush=True)
    return out


def grouped_statewide(url, where, st, key):
    rows, offset = [], 0
    while True:
        d, full = get(url, {"where": where, "groupByFieldsForStatistics": "county_id,f_system,ownership",
                            "outStatistics": STATS, "resultOffset": offset,
                            "resultRecordCount": 1000, "orderByFields": "county_id,f_system,ownership",
                            "f": "json"}, tries=2)
        feats = [f["attributes"] for f in d.get("features", [])]
        rows += feats
        print("   ", st, key, "offset", offset, len(feats), flush=True)
        if len(feats) < 1000:
            return rows
        offset += 1000


def grouped_by_county(url, where, st):
    import csv
    import geopandas as gpd
    codes = {r["abbr"]: r["fips_state"] for r in csv.DictReader(open(os.path.join(ROOT, "code", "state_codes.csv")))}
    cty = gpd.read_file(os.path.join(ROOT, "data", "raw", "census", "tl_2020_us_county.zip"), columns=["STATEFP", "COUNTYFP"], ignore_geometry=True)
    rows = []
    for cf in sorted(cty[cty.STATEFP == codes[st]].COUNTYFP.astype(int)) + [None]:
        w = where + (f" AND county_id = {cf}" if cf is not None else " AND county_id IS NULL")
        d, _ = get(url, {"where": w, "groupByFieldsForStatistics": "f_system,ownership", "outStatistics": STATS, "f": "json"})
        rows += [{**f["attributes"], "county_id": cf} for f in d.get("features", [])]
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    for st in STATES:
        dest = os.path.join(OUT, f"hpms_{YEAR}_{st}_county_fsys_owner.json")
        if os.path.exists(dest):
            print("skip", st, flush=True)
            continue
        url = BASE.format(st=st, y=YEAR)
        result = {"state": st, "year": YEAR, "service": url, "where": WHERE, "rows": {}}
        for key, where in WHERE.items():
            try:
                result["rows"][key] = grouped_statewide(url, where, st, key)
            except RuntimeError:
                # Large states (California) can time out on one statewide query:
                # ask county by county instead, plus one query for blank county codes.
                print("   ", st, key, "statewide query failed; asking county by county", flush=True)
                result["rows"][key] = grouped_by_county(url, where, st)
        nulls = sum(r["miles"] or 0 for r in result["rows"]["all"] if r["county_id"] is None)
        total = sum(r["miles"] or 0 for r in result["rows"]["all"])
        result["blank_county_miles"] = nulls
        if total and nulls / total > 0.005:
            import csv
            codes = {r["abbr"]: r["fips_state"] for r in csv.DictReader(open(os.path.join(ROOT, "code", "state_codes.csv")))}
            sp = spatial_pass(st, url, codes[st])
            result["spatial_rows"] = sp
            print("  spatial pass", st, round(nulls), "blank-county miles", flush=True)
        with open(dest, "w") as f:
            json.dump(result, f)
        subprocess.run([sys.executable, PROV, dest, url, "--log", LOG,
                        "--note", "FHWA HPMS 2024 full extent, server-side sum of SECTIONLENGTH grouped by county_id,f_system,ownership; filters in file"],
                       check=True, stdout=subprocess.DEVNULL)
        print("ok", st, len(result["rows"]["all"]), len(result["rows"]["rural"]), flush=True)


if __name__ == "__main__":
    main()
