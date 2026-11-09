"""Build the reading copy MANUSCRIPT_draft_v1.docx from MANUSCRIPT_draft_v1.md: insert Tables 1 to 3 from
paper_figures/out/tables.md at their [[TABLEn]] markers and Figures 1 to 6 (PNG) with their captions after the
section that first cites them. The figure captions section is kept at the end, as the journal asks."""
import os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "paper_figures", "out")
md = open(os.path.join(HERE, "MANUSCRIPT_draft_v1.md"), encoding="utf-8").read()
tables = open(os.path.join(FIG, "tables.md"), encoding="utf-8").read()
blocks = {int(m.group(1)): m.group(0).strip() for m in re.finditer(r"\*\*Table (\d)\.\*\*.*?(?=\n\*\*Table \d\.\*\*|\Z)", tables, re.S)}
for k, b in blocks.items():
    md = md.replace(f"[[TABLE{k}]]", b)
caps = dict(re.findall(r"\*\*Fig\. (\d)\.\*\* (.*)", md))
files = {1: "fig1_overview", 2: "fig2_validation", 3: "fig3_tank", 4: "fig4_material_transfer", 5: "fig5_quantity", 6: "fig6_examples"}
before = {1: "# 2. Dataset", 2: "# 4. Benchmark", 3: "## 5.2 PCM", 4: "## 5.3 Reproducibility", 5: "## 5.3 Reproducibility", 6: "# 6. Discussion"}
for k in (1, 2, 3, 4, 5, 6):
    img = f"![**Fig. {k}.** {caps[str(k)]}]({os.path.join(FIG, files[k] + '.png').replace(os.sep, '/')}){{width=16.5cm}}\n\n"
    i = md.index(before[k])
    md = md[:i] + img + md[i:]
tmp = os.path.join(HERE, "_build.md")
open(tmp, "w", encoding="utf-8").write(md)
out = os.path.join(HERE, "MANUSCRIPT_draft_v1.docx")
subprocess.run(["pandoc", tmp, "-o", out, "--resource-path", FIG], check=True)
os.remove(tmp)
print("wrote", out)
