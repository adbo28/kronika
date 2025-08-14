
## Postupy

### Generování

uv run py kro2md.py
zkopírovat md soubory do zdroje pro MkDocs (copy_chapters.bat)
Zkontroluj mkdocs.yml v docs-site/ složce
Zkontrluj docs-site/docs/index.md
Spuštění dev serveru (cd docs-site; uv run mkdocs serve)
Build statických souborů (uv run mkdocs build)

???
Deploy na github pages
uv run mkdocs gh-deploy



