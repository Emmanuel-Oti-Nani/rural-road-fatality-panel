#!/usr/bin/env python3
"""
10_preprint_tex.py - Write and compile the validation preprint (REVTeX 4.2, two columns).

PLAIN-LANGUAGE NOTE: Builds paper/preprint/main.tex from paper/stats.json and the
validation tables, then compiles it to paper/preprint/main.pdf. Every number in the
text is filled in from those files. To add the Zenodo DOI once it exists, run:
    python code/10_preprint_tex.py --doi 10.5281/zenodo.NNNNNNN
Requires a TeX installation with REVTeX 4.2 (included in TeX Live as "revtex").
"""
import argparse
import json
import os
import subprocess

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "paper", "validation_tables")
O = os.path.join(ROOT, "paper", "preprint")
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
A = json.load(open(os.path.join(ROOT, "AUTHORS.json")))["authors"][0]
V = S["validation"]
OV = V["overall_deaths"]
OC = V["overall_crashes"]
Y = {int(k): v for k, v in V["by_year"].items()}
E, L = V["period_2015_2019"], V["period_2020_2024"]
D = V["census_rural_distance_to_urban_area"]
R = {int(k): v for k, v in S["rural_by_year"].items()}


def n(x):
    return f"{int(round(x)):,}".replace(",", "{,}")


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def table_years():
    rows = []
    for y in sorted(Y):
        r = Y[y]
        rows.append(f"{y} & {n(r['n'])} & {f1(r['pct_agree'])} & {r['kappa']:.3f} & {f1(r['sensitivity_fars_rural'])} & "
                    f"{f1(r['specificity_fars_rural'])} & {f1(r['pct_rural_census'])} & {f1(r['pct_rural_fars'])} \\\\")
    return "\n".join(rows)


def table_road():
    rd = pd.read_csv(os.path.join(T, "agreement_by_road_class.csv"))
    names = {"interstate_fwy": "Interstate, freeway", "arterial": "Arterial",
             "collector": "Collector", "local": "Local"}
    out = []
    for k in ["interstate_fwy", "arterial", "collector", "local"]:
        r = rd[rd.road_class == k].iloc[0]
        out.append(f"{names[k]} & {n(r.n)} & {f1(r.pct_agree)} & {r.kappa:.3f} & {f1(r.sensitivity_fars_rural)} & {f1(r.specificity_fars_rural)} \\\\")
    return "\n".join(out)


def table_states():
    dv = pd.read_csv(os.path.join(T, "state_divergence_2015_16_vs_2023_24.csv"))
    big = dv[dv.deaths_2015_16_and_2023_24 >= 2000]
    sel = pd.concat([big.head(6), big.tail(2)])
    st = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).set_index("abbr").state_name
    out = []
    for i, r in enumerate(sel.itertuples()):
        if i == 6:
            out.append("\\hline")
        out.append(f"{st[r.state]} & {n(r.deaths_2015_16_and_2023_24)} & {f1(r.fars_2015_16)} & {f1(r.fars_2023_24)} & "
                   f"{f1(r.census_2015_16)} & {f1(r.census_2023_24)} & {r.divergence:+.1f} \\\\")
    return "\n".join(out), big


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", default="")
    a = ap.parse_args()
    doi_text = (f"\\href{{https://doi.org/{a.doi}}}{{doi:{a.doi}}}" if a.doi else
                "Zenodo (DOI assigned at release)")
    st_rows, big = table_states()
    dv = pd.read_csv(os.path.join(T, "state_divergence_2015_16_vs_2023_24.csv"))
    yr = pd.read_csv(os.path.join(T, "fars_rural_share_by_state_year.csv"), index_col=0)
    lowst = pd.read_csv(os.path.join(T, "agreement_by_state_2022_2024.csv"))
    lowst = lowst[lowst.n >= 500].sort_values("pct_agree")  # small states rest on too few deaths
    big_states = big.sort_values("divergence")
    names = pd.read_csv(os.path.join(ROOT, "code", "state_codes.csv"), dtype=str).set_index("abbr").state_name
    ny, ca = yr.loc["NY"], yr.loc["CA"]
    nat_drop = Y[2015]["pct_rural_fars"] - Y[2024]["pct_rural_fars"]
    cen_drop = Y[2015]["pct_rural_census"] - Y[2024]["pct_rural_census"]
    tok = {
        "TITLE": "How Rural Is Rural? Agreement Between the FARS Rural/Urban Label and 2020 Census Urban Areas for U.S.\\ Traffic Deaths, 2015--2024",
        "NAME": A["name"], "ORCID": A["orcid"], "EMAIL": A["email"],
        "CR": n(V["crashes_compared"]), "CALL": n(V["crashes_all"]), "DC": n(V["deaths_compared"]),
        "PCTC": f1(V["crashes_compared"] / V["crashes_all"] * 100), "CEX": n(V["crashes_excluded"]),
        "AGREE": f1(OV["pct_agree"]), "KAPPA": f"{OV['kappa']:.2f}", "KAPPA3": f"{OV['kappa']:.3f}",
        "SENS": f1(OV["sensitivity_fars_rural"]), "MISS": f1(100 - OV["sensitivity_fars_rural"]), "SPEC": f1(OV["specificity_fars_rural"]),
        "FP": f1(100 - OV["specificity_fars_rural"]),
        "A": n(OV["both_rural"]), "B": n(OV["census_rural_fars_urban"]), "C": n(OV["census_urban_fars_rural"]), "D": n(OV["both_urban"]),
        "AR": n(OV["both_rural"] + OV["census_rural_fars_urban"]), "AU": n(OV["census_urban_fars_rural"] + OV["both_urban"]),
        "FR": n(OV["both_rural"] + OV["census_urban_fars_rural"]), "FU": n(OV["census_rural_fars_urban"] + OV["both_urban"]),
        "N": n(OV["n"]), "RC": f1(OV["pct_rural_census"]), "RF": f1(OV["pct_rural_fars"]),
        "Y15C": f1(Y[2015]["pct_rural_census"]), "Y15F": f1(Y[2015]["pct_rural_fars"]),
        "Y24C": f1(Y[2024]["pct_rural_census"]), "Y24F": f1(Y[2024]["pct_rural_fars"]),
        "GAP15": f1(Y[2015]["pct_rural_census"] - Y[2015]["pct_rural_fars"]), "GAP24": f1(Y[2024]["pct_rural_census"] - Y[2024]["pct_rural_fars"]),
        "NATDROP": f1(nat_drop), "CENDROP": f1(cen_drop),
        "SENS15": f1(Y[2015]["sensitivity_fars_rural"]), "SENS24": f1(Y[2024]["sensitivity_fars_rural"]),
        "SPEC15": f1(Y[2015]["specificity_fars_rural"]), "SPEC24": f1(Y[2024]["specificity_fars_rural"]),
        "KE": f"{E['kappa']:.3f}", "KL": f"{L['kappa']:.3f}",
        "R15C": n(R[2015]["rural_census"]), "R24C": n(R[2024]["rural_census"]), "R15F": n(R[2015]["rural_fars"]), "R24F": n(R[2024]["rural_fars"]),
        "DIFF24": n(R[2024]["rural_census"] - R[2024]["rural_fars"]),
        "DMU": f2(D["urban"]["median_km"]), "DMR": f2(D["rural"]["median_km"]),
        "DU1": f1(D["urban"]["pct_within_1km"]), "DR1": f1(D["rural"]["pct_within_1km"]),
        "DU5": f1(D["urban"]["pct_within_5km"]), "DR5": f1(D["rural"]["pct_within_5km"]),
        "CAGREE": f1(OC["pct_agree"]), "CKAPPA": f"{OC['kappa']:.3f}", "CSENS": f1(OC["sensitivity_fars_rural"]),
        "CRC": f1(OC["pct_rural_census"]), "CRF": f1(OC["pct_rural_fars"]),
        "MINN": "500", "NBIGNEG": str(int((big.divergence <= -5).sum())), "NBIG": str(len(big)),
        "NNEG": str(V["states_divergence_below_minus5"]), "NPOS": str(V["states_divergence_above_plus5"]),
        "NY17": f1(ny["2017"]), "NY18": f1(ny["2018"]), "CA17": f1(ca["2017"]), "CA18": f1(ca["2018"]),
        "NYDIV": f1(-dv.set_index("state").loc["NY"].divergence), "CADIV": f1(-dv.set_index("state").loc["CA"].divergence),
        "LOWAGREE": f1(lowst.iloc[0].pct_agree), "LOWSTATE": names[lowst.iloc[0].state],
        "HIGHAGREE": f1(lowst.iloc[-1].pct_agree), "HIGHSTATE": names[lowst.iloc[-1].state],
        "NH24T": n(S["nhtsa_2024"]["total"]), "NH24R": n(S["nhtsa_2024"]["rural"]),
        "DEATHS": n(S["deaths_total"]), "CRASHES": n(S["crashes_total"]),
        "YEARROWS": table_years(), "ROADROWS": table_road(), "STATEROWS": st_rows,
        "DOI": doi_text, "REPO": f"https://github.com/{A['github']}/rural-road-fatality-panel",
        "ATLAS": f"https://{A['github'].lower()}.github.io/rural-road-fatality-panel/",
    }
    tex = open(os.path.join(ROOT, "code", "preprint_template.tex")).read()
    for k, v in tok.items():
        tex = tex.replace(f"<<{k}>>", v)
    left = [line for line in tex.splitlines() if "<<" in line]
    if left:
        raise SystemExit("Unfilled tokens: " + " | ".join(left[:5]))
    os.makedirs(O, exist_ok=True)
    open(os.path.join(O, "main.tex"), "w").write(tex)
    for _ in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=O,
                           capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:])
        raise SystemExit("pdflatex failed")
    print("wrote paper/preprint/main.pdf")


if __name__ == "__main__":
    main()
