@echo off

REM Smazání cílových adresářů (pokud existují)
rmdir /s /q "output\chapters"
rmdir /s /q "output\indexes"
rmdir /s /q "docs-site\docs\chapters"
rmdir /s /q "docs-site\docs\indexes"

REM Znovuvytvoření adresářů
mkdir "output\chapters"
mkdir "output\indexes"
mkdir "docs-site\docs\chapters"
mkdir "docs-site\docs\indexes"

REM uv run py md_create.py

uv run py md_process.py

uv run py md_split.py

REM Kopírování souborů
copy ".\output\chapters\*.md" "docs-site\docs\chapters\" > NUL
copy ".\output\indexes\*.md" "docs-site\docs\indexes\" > NUL

uv run py generate_nav.py

echo Hotovo!