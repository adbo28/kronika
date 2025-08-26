# Municipal Chronicle of Stará Ves (1923-1991)

A digitized 400-page Czech municipal chronicle covering 150 years of local history, converted to a searchable website.

## 🌐 Live Demo
[https://adbo28.github.io/kronika/](https://adbo28.github.io/kronika/)

## 📖 About
Converts a historical Czech municipal chronicle (1923-1991) from PDF to a responsive website with hierarchical navigation, full-text search, and mobile-friendly design.

## 🛠️ Tech Stack
- **PDF Processing**: PyMuPDF4LLM
- **Site Generator**: MkDocs with Material theme
- **Package Manager**: uv
- **Deployment**: GitHub Pages

## 🚀 Quick Start
```bash
git clone https://github.com/adbo28/kronika.git
cd kronika
uv sync
cd docs-site
uv run mkdocs serve
```

## 🔧 Scripts

1. md_create - convert pdf to one large md file. Fix smaller things like page breaks and soft hyphens.
2. md_process - read the large md file and build indexes. The script builds three (TODO) indexes - by address number, by name and by year. The script uses regex and other rules to process the input document, but it also supports a pattern file that allows specific places in the initial document to be black- or white-listed. It generates extracted_patterns.txt which is mainly intended for human control and index.json which is used for further processing.
3. md_split - TODO

Helper scripts

* name_to_base_form - creates name_nase_form.jsonl based on extracted_patterns.txt. Using AI, it tries to group names by base form (e.g. Adama Noska --> Adam Nosek) so that we can build an index by names. The jsonl file is supposed to be used as a translation dict. It condenced the total 18k names to 8671 values and 6027 values in base form.
* build_vocab - generates word_counts.json
* generate_nav - TODO


## 🔧 Workflow

```bash
uv run python kro2md.py - Convert PDF
copy_chapters.bat - Copy files
uv run python generate_nav.py - Generate navigation
uv run mkdocs serve - Local preview
uv run mkdocs gh-deploy - Deploy
```