#!/usr/bin/env python3
"""
12_eartharxiv.py - Build the EarthArXiv submission version of the preprint (Word and PDF).

PLAIN-LANGUAGE NOTE: EarthArXiv asks for one PDF that (1) states on a cover sheet
that it is a non-peer-reviewed preprint submitted to EarthArXiv, (2) shows the
author's full ORCID link at the top, and (3) contains title, abstract, authors,
affiliations, and a correspondence email, with all material in a single file.
This script takes the verified preprint text (paper/preprint/main.tex, whose
numbers come from paper/stats.json) and lays it out that way: cover sheet,
running header on every page, single column, line numbers, numbered sections,
tables and figures in the text. It writes paper/eartharxiv/ ...docx and ...pdf.

Requires pandoc and LibreOffice (for the PDF).
"""
import os
import re
import subprocess

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "paper", "preprint")
OUT = os.path.join(ROOT, "paper", "eartharxiv")
os.makedirs(OUT, exist_ok=True)
NAME = "Nani_2026_FARS_rural_urban_EarthArXiv_preprint"
HEADER = "Non-peer-reviewed preprint submitted to EarthArXiv"
ORCID = "https://orcid.org/0009-0009-4175-8962"

tex = open(os.path.join(SRC, "main.tex")).read()
title = re.search(r"\\title\{(.+?)\}\n", tex).group(1).replace("\\ ", " ").replace("--", "–")
abstract = re.search(r"\\begin\{abstract\}(.+?)\\\\\[4pt\]", tex, re.S).group(1).strip()
keywords = re.search(r"\\textbf\{Keywords:\}(.+?)\n", tex).group(1).strip()
body = tex[tex.index("\\maketitle") + len("\\maketitle"): tex.index("\\begin{thebibliography}")]
bib = re.findall(r"\\bibitem\{(.+?)\}\s*(.+?)(?=\n\n|\n\\end\{thebibliography\})", tex, re.S)
order = {k: i + 1 for i, (k, _) in enumerate(bib)}

# --- cross-references: Arabic numbering for a single-column manuscript
REF = {"sec:data": "Section 2", "sec:methods": "Section 3", "sec:results": "Section 4", "sec:discussion": "Section 5",
       "tab:twobytwo": "1", "tab:years": "2", "tab:road": "3", "tab:states": "4",
       "fig:share": "1", "fig:distance": "2", "fig:states": "3"}


def cites(m):
    nums = [order[k.strip()] for k in m.group(1).split(",")]
    return "[" + ", ".join(str(x) for x in nums) + "]"


def fix(s):
    s = re.sub(r"~?\\cite\{([^}]+)\}", lambda m: " " + cites(m), s)
    s = re.sub(r"Section~\\ref\{(sec:\w+)\}", lambda m: REF[m.group(1)], s)
    s = re.sub(r"Sec\.~\\ref\{(sec:\w+)\}", lambda m: REF[m.group(1)], s)
    s = re.sub(r"Table~\\ref\{(tab:\w+)\}", lambda m: "Table " + REF[m.group(1)], s)
    s = re.sub(r"Fig\.~\\ref\{(fig:\w+)\}", lambda m: "Figure " + REF[m.group(1)], s)
    s = re.sub(r"\\label\{[^}]+\}", "", s)
    return s


body = fix(body)
abstract = fix(abstract)
# EarthArXiv scope: say plainly that this is a geographic (GIS) classification problem
body = body.replace(
    "Highway agencies then updated their adjusted boundaries on their own schedules.",
    "Highway agencies then updated their adjusted boundaries on their own schedules. The question is therefore a "
    "geographic one: two boundary systems, drawn for different purposes, classify the same crash locations, and "
    "a point-in-polygon analysis can measure how far they agree.")
body = body.replace("Agreement (\\%) & $\\kappa$ & $S_e$ (\\%) & $S_p$ (\\%) & Rural, Census map (\\%) & Rural, FARS label (\\%)", "Agree (\\%) & $\\kappa$ & $S_e$ (\\%) & $S_p$ (\\%) & Rural, Census (\\%) & Rural, FARS (\\%)")
body = body.replace("\\begin{ruledtabular}", "").replace("\\end{ruledtabular}", "")
body = body.replace("\\begin{table*}", "\\begin{table}").replace("\\end{table*}", "\\end{table}")
body = re.sub(r"\{(fig\d_\w+)\.pdf\}", lambda m: "{" + os.path.join(SRC, m.group(1) + ".png") + "}", body)
body = body.replace("\\section*{Data availability}", "\\section*{Data and code availability}")
refs = "\n".join(f"\\noindent [{order[k]}] " + re.sub(r"\s+", " ", v).strip() + "\n" for k, v in bib)

doc_tex = r"""\documentclass{article}
\usepackage{amsmath}\usepackage{graphicx}\usepackage{hyperref}
\begin{document}
""" + body + "\n\\section*{References}\n" + refs + "\n\\end{document}\n"
work = os.path.join(OUT, "build")
os.makedirs(work, exist_ok=True)
open(os.path.join(work, "body.tex"), "w").write(doc_tex)
subprocess.run(["pandoc", os.path.join(work, "body.tex"), "-f", "latex", "-t", "docx", "--number-sections",
                "-o", os.path.join(work, "body.docx")], check=True)

# --- assemble: cover sheet + title page, then body
d = docx.Document(os.path.join(work, "body.docx"))
FONT = "Times New Roman"
for sty in d.styles:
    try:
        if sty.font is not None:
            sty.font.name = FONT
            rpr = sty.element.get_or_add_rPr()
            rfonts = rpr.find(qn("w:rFonts"))
            if rfonts is None:
                rfonts = OxmlElement("w:rFonts")
                rpr.append(rfonts)
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rfonts.set(qn(a), FONT)
            if sty.font.color is not None and sty.name.startswith("Heading"):
                sty.font.color.rgb = RGBColor(0, 0, 0)
    except (AttributeError, ValueError):
        pass
for nm, size in [("Normal", 12), ("Body Text", 12), ("First Paragraph", 12), ("Heading 1", 14), ("Heading 2", 12),
                 ("Table Caption", 11), ("Image Caption", 11), ("Compact", 11)]:
    smap = {x.name: x for x in d.styles}
    if nm in smap:
        st = smap[nm]
        st.font.size = Pt(size)
        pf = st.paragraph_format
        if nm in ("Body Text", "First Paragraph", "Normal"):
            pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            pf.space_after = Pt(8)
        if nm.startswith("Heading"):
            st.font.bold = True
            st.font.italic = False
            pf.space_before = Pt(14)
            pf.space_after = Pt(6)
        if nm.endswith("Caption"):
            st.font.italic = False

first = d.paragraphs[0]


def before(text="", style=None, bold=False, size=None, align=None, italic=False, link=None, after=6):
    p = first.insert_paragraph_before("", style=style)
    if text:
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        r.font.name = FONT
        if size:
            r.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    return p


C = WD_ALIGN_PARAGRAPH.CENTER
# Cover sheet (EarthArXiv template wording, Option 1)
before("This is a non-peer-reviewed preprint submitted to EarthArXiv.", bold=True, size=14, align=C, after=18)
before(title, bold=True, size=16, align=C, after=12)
before("Emmanuel Oti Nani", bold=True, size=12, align=C, after=2)
before("Independent Researcher, Springfield, Missouri, USA", size=12, align=C, after=2)
before("ORCID: " + ORCID, size=12, align=C, after=2)
before("Correspondence: en289s@missouristate.edu", size=12, align=C, after=18)
before("This manuscript is a preprint and has not been peer reviewed. It has not yet been submitted to a journal. "
       "Subsequent versions of this manuscript may have slightly different content. If accepted for publication, "
       "the final version will be available via the 'Peer-reviewed Publication DOI' link on the right-hand side of "
       "the EarthArXiv webpage. Please feel free to contact the author; feedback is welcome.", size=12, align=C, after=12)
before("Data and code: https://doi.org/10.5281/zenodo.23547650", size=12, align=C, after=0)
pb = before()
pb.add_run().add_break(docx.enum.text.WD_BREAK.PAGE)
# Title page of the manuscript itself
before(title, bold=True, size=15, align=C, after=10)
before("Emmanuel Oti Nani", bold=True, size=12, align=C, after=2)
before("Independent Researcher, Springfield, Missouri, USA  |  " + ORCID + "  |  en289s@missouristate.edu",
       size=11, align=C, after=14)
h = before("Abstract", style={x.name: x for x in d.styles}["Heading 1"])
abs_plain = subprocess.run(["pandoc", "-f", "latex", "-t", "plain", "--wrap=none"], input=abstract, capture_output=True,
                           text=True, check=True).stdout.strip()
before(abs_plain, style={x.name: x for x in d.styles}["Body Text"])
kp = before("", style={x.name: x for x in d.styles}["Body Text"])
kp.add_run("Keywords: ").bold = True
kp.add_run(keywords.replace("road safety data", "road safety data, geographic information science, spatial analysis"))

# Running header (Option 2) and page numbers, line numbers on every page
sec = d.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Inches(1))
hp = sec.header.paragraphs[0]
hp.text = HEADER
hp.alignment = C
for r in hp.runs:
    r.font.size, r.font.italic, r.font.name = Pt(9), True, FONT
fp = sec.footer.paragraphs[0]
fp.alignment = C


def field(par, instr):
    r = par.add_run()
    for tag, txt in (("begin", None), (None, instr), ("end", None)):
        if tag:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), tag)
            r._r.append(e)
        else:
            t = OxmlElement("w:instrText")
            t.set(qn("xml:space"), "preserve")
            t.text = txt
            r._r.append(t)


for par in (hp, fp):
    par._p.get_or_add_pPr().append(OxmlElement("w:suppressLineNumbers"))
fp.add_run("Page ")
field(fp, "PAGE")
ln = OxmlElement("w:lnNumType")
ln.set(qn("w:countBy"), "1")
ln.set(qn("w:restart"), "continuous")
ln.set(qn("w:distance"), "360")
sec._sectPr.append(ln)

# Figures: fit to text width; tables: simple ruled style, centered
for shp in d.inline_shapes:
    ratio = shp.height / shp.width
    shp.width = Inches(5.5)
    shp.height = int(Inches(5.5) * ratio)
for t in d.tables:
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl = t._tbl
    pr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "insideH"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "808080")
        borders.append(e)
    pr.append(borders)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(10)
# no line numbers inside tables (keeps them readable)
for t in d.tables:
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                ppr = p._p.get_or_add_pPr()
                s = OxmlElement("w:suppressLineNumbers")
                ppr.append(s)

# Number captions ("Table 1.", "Figure 1.") as in the PDF
nt = nf = 0
for p in d.paragraphs:
    sn = p.style.name if p.style is not None else ""
    if sn in ("Table Caption", "Image Caption") and p.text.strip():
        if sn == "Table Caption":
            nt += 1
            lab = f"Table {nt}. "
        else:
            nf += 1
            lab = f"Figure {nf}. "
        r0 = p.runs[0]
        new = p._p.makeelement(qn("w:r"), {})
        p._p.insert(list(p._p).index(r0._r), new)
        from docx.text.run import Run
        rr = Run(new, p)
        rr.text = lab
        rr.bold = True
        rr.font.name = FONT
        rr.font.size = Pt(11)
print("captions numbered:", nt, "tables,", nf, "figures")
out_docx = os.path.join(OUT, NAME + ".docx")
d.core_properties.title = title
d.core_properties.author = "Emmanuel Oti Nani"
d.save(out_docx)

# --- PDF: typeset with LaTeX (LibreOffice cannot render Word equations here), same text and layout rules
kw_tex = keywords.replace("road safety data", "road safety data, geographic information science, spatial analysis")
pdf_tex = r"""\documentclass[12pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{mathptmx}\usepackage{amsmath}\usepackage{graphicx}\usepackage{setspace}\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}\usepackage[right]{lineno}\usepackage[font=small,labelfont=bf]{caption}\usepackage{orcidlink}\usepackage{xurl}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0.4pt}
\fancyhead[C]{\small\itshape """ + HEADER + r"""}\fancyfoot[C]{\small Page \thepage}
\fancypagestyle{plain}{\fancyhf{}\fancyhead[C]{\small\itshape """ + HEADER + r"""}\fancyfoot[C]{\small Page \thepage}}
\setcounter{secnumdepth}{2}
\begin{document}
\begin{titlepage}\thispagestyle{fancy}\centering
{\large\bfseries This is a non-peer-reviewed preprint submitted to EarthArXiv.\par}\vspace{1.2cm}
{\Large\bfseries """ + title.replace("–", "--") + r"""\par}\vspace{0.8cm}
{\bfseries Emmanuel Oti Nani}\,\orcidlink{0009-0009-4175-8962}\par
Independent Researcher, Springfield, Missouri, USA\par
ORCID: \url{""" + ORCID + r"""}\par
Correspondence: \href{mailto:en289s@missouristate.edu}{en289s@missouristate.edu}\par\vspace{1.2cm}
\begin{minipage}{0.85\textwidth}\centering
This manuscript is a preprint and has not been peer reviewed. It has not yet been submitted to a journal.
Subsequent versions of this manuscript may have slightly different content. If accepted for publication, the
final version will be available via the `Peer-reviewed Publication DOI' link on the right-hand side of the
EarthArXiv webpage. Please feel free to contact the author; feedback is welcome.\end{minipage}\par\vspace{0.8cm}
Data and code: \url{https://doi.org/10.5281/zenodo.23547650}\par
\end{titlepage}\setcounter{page}{2}
\linenumbers\onehalfspacing
\begin{center}{\large\bfseries """ + title.replace("–", "--") + r"""\par}\vspace{0.3cm}
{\bfseries Emmanuel Oti Nani}\par{\small Independent Researcher, Springfield, Missouri, USA $\mid$ \url{""" + ORCID + r"""} $\mid$ en289s@missouristate.edu\par}\end{center}
\section*{Abstract}
""" + abstract + r"""\par\medskip
\noindent\textbf{Keywords:} """ + kw_tex + "\n" + body.replace("\\begin{table}[t]", "\\begin{table}[htbp]\\centering\\small").replace("\\begin{figure}[t]", "\\begin{figure}[htbp]\\centering").replace("width=\\columnwidth", "width=0.8\\textwidth") + "\n\\section*{References}\n{\\small " + refs + "}\n\\end{document}\n"
pdf_tex = re.sub(r"\\href\{(https://doi\.org/[^}]+)\}\{doi:[^}]+\}", r"\\url{\1}", pdf_tex)  # breakable DOI links
open(os.path.join(work, "ea.tex"), "w").write(pdf_tex)
for _ in range(2):
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "ea.tex"], cwd=work, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout[-2500:])
    raise SystemExit("pdflatex failed")
import shutil
shutil.copy(os.path.join(work, "ea.pdf"), os.path.join(OUT, NAME + ".pdf"))
print("wrote", out_docx, "and", os.path.join(OUT, NAME + ".pdf"))
