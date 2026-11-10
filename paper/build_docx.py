"""Build MANUSCRIPT_draft_v1.docx from MANUSCRIPT_draft_v1.md in the RP2 house style.

- Styles, fonts, page size, margins and footer come from the RP2 manuscript used as pandoc's reference
  document (Review_Paper_2/MANUSCRIPT_RP2_numbered.docx), as for RP2 itself.
- Tables 1 to 3 are inserted from paper_figures/out/tables.md at their [[TABLEn]] markers, with the bold
  "Table n." caption above (RP2 convention).
- Figures 1 to 6 (PNG) are inserted after the section that first cites them, each followed by an italic
  "Figure n." caption (RP2 convention); caption texts come from figure_captions.md.
"""
import os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.dirname(os.path.dirname(HERE))
FIG = os.path.join(os.path.dirname(HERE), "paper_figures", "out")
REF = os.path.join(PUB, "Review_Paper_2", "MANUSCRIPT_RP2_numbered.docx")
import sys
VER = sys.argv[1] if len(sys.argv) > 1 else "v1"   # 2026-11-10: "v2" builds the revised draft
md = open(os.path.join(HERE, f"MANUSCRIPT_draft_{VER}.md"), encoding="utf-8").read()
tables = open(os.path.join(FIG, "tables.md"), encoding="utf-8").read()
blocks = {int(m.group(1)): m.group(0).strip() for m in re.finditer(r"\*\*Table (\d)\.\*\*.*?(?=\n\*\*Table \d\.\*\*|\Z)", tables, re.S)}
for k, b in blocks.items():
    # RP2: bold caption title; keep the rest of the caption plain
    b = re.sub(r"^\*\*Table (\d)\.\*\* ([^.]*\.)", r"**Table \1. \2**", b)
    md = md.replace(f"[[TABLE{k}]]", b)
caps = dict(re.findall(r"\*\*Fig\. (\d)\.\*\* (.*)", open(os.path.join(HERE, "figure_captions.md"), encoding="utf-8").read()))
files = {1: "fig1_overview", 2: "fig2_validation", 3: "fig3_tank", 4: "fig4_material_transfer", 5: "fig5_quantity", 6: "fig6_examples"}
before = {1: "# 2. Dataset", 2: "# 4. Benchmark", 3: "## 5.2 PCM", 4: "## 5.3 Reproducibility", 5: "## 5.3 Reproducibility", 6: "# 6. Discussion"}
for k in (1, 2, 3, 4, 5, 6):
    path = os.path.join(FIG, files[k] + ".png").replace(os.sep, "/")
    blk = f"![]({path}){{width=16cm}}\n\n*Figure {k}. {caps[str(k)]}*\n\n"
    i = md.index(before[k])
    md = md[:i] + blk + md[i:]
tmp = os.path.join(HERE, "_build.md")
open(tmp, "w", encoding="utf-8").write(md)
out = os.path.join(HERE, f"MANUSCRIPT_draft_{VER}.docx")
subprocess.run(["pandoc", tmp, "-f", "markdown-implicit_figures", "-o", out, "--reference-doc", REF, "--resource-path", FIG], check=True)
os.remove(tmp)

# RP2 table style (as in MANUSCRIPT_RP2_numbered.docx): three horizontal rules only (top 1 pt, under the
# header 0.5 pt, bottom 1 pt), no vertical lines, Arial, single line spacing with 1 pt before/after,
# first column left, other columns centred, cells vertically centred. Size 9 pt (RP2: 11 pt) because
# Table 3 has seven columns.
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

doc = docx.Document(out)


def borders(cell, top=None, bottom=None):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(old)
    b = OxmlElement("w:tcBorders")
    for side, sz in (("top", top), ("left", None), ("bottom", bottom), ("right", None), ("insideH", None), ("insideV", None)):
        e = OxmlElement(f"w:{side}")
        if sz:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), "000000")
        else:
            e.set(qn("w:val"), "nil")
        b.append(e)
    tcPr.append(b)
    v = OxmlElement("w:vAlign"); v.set(qn("w:val"), "center"); tcPr.append(v)


for t in doc.tables:
    n = len(t.rows)
    for i, row in enumerate(t.rows):
        for j, cell in enumerate(row.cells):
            borders(cell, top=8 if i == 0 else None, bottom=4 if i == 0 else (8 if i == n - 1 else None))
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                pf = p.paragraph_format
                pf.line_spacing = 1.0; pf.space_before = Pt(1); pf.space_after = Pt(1)
                for r in p.runs:
                    r.font.name = "Arial"; r.font.size = Pt(9)
                    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial"); r._element.rPr.rFonts.set(qn("w:cs"), "Arial")
doc.save(out)
print("wrote", out)
