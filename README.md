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

## 🔧 Workflow

```bash
uv run python kro2md.py - Convert PDF
copy_chapters.bat - Copy files
uv run python generate_nav.py - Generate navigation
uv run mkdocs serve - Local preview
uv run mkdocs gh-deploy - Deploy
```