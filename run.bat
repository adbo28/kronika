@echo off

REM Smazání a znovuvytvoření generovaných adresářů
rmdir /s /q "output\chapters"
rmdir /s /q "output\indexes"
rmdir /s /q "docs-site\docs\chapters"
rmdir /s /q "docs-site\docs\indexes"

mkdir "output\chapters"
mkdir "output\indexes"
mkdir "docs-site\docs\chapters"
mkdir "docs-site\docs\indexes"

uv run py md_process.py
uv run py md_split.py

REM Kopírování do docs-site
copy ".\output\chapters\*.md" "docs-site\docs\chapters\" > NUL
copy ".\output\indexes\*.md" "docs-site\docs\indexes\" > NUL

uv run py md_generate_nav.py

echo Hotovo!
