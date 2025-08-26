import pathlib
import yaml
import re

INPUT_MD_FILE = "./data/output.md"
OUTPUT_DIR = "output_chapters"


def extract_heading_info(line):
    """Extrahuje informace o nadpisu z markdown řádky"""
    match = re.match(r'^(#{1,3})\s+(.+)$', line.strip())
    if match:
        hashes = match.group(1)
        title = match.group(2).strip()
        title = clean_title(title)
        level = len(hashes)
        return title, level
    return None, None


def create_chapter_file(content_lines, title, chapter_num, level):
    """Vytvoří markdown obsah s YAML frontmatter"""
    frontmatter = {
        'title': title,
        'chapter_number': chapter_num,
        'heading_level': level,
        'nav_weight': chapter_num,  # pro řazení v navigaci
    }
    
    yaml_header = yaml.dump(frontmatter, 
                           allow_unicode=True, 
                           default_flow_style=False,
                           sort_keys=False)
    
    # Spojení obsahu kapitoly (bez původního nadpisu)
    content = '\n'.join(content_lines)
    
    full_content = f"---\n{yaml_header}---\n\n{content}"
    
    filename = f"chapter_{chapter_num:03d}.md"
    return filename, full_content


def clean_title(title):
    """Odstraní markdown formátování z názvu kapitoly"""
    # Odstraň bold formátování **text**
    title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)
    # Odstraň italic formátování *text*
    title = re.sub(r'\*(.*?)\*', r'\1', title)
    # Odstraň další případné formátování
    title = title.strip()
    return title


def main():
    # Kontrola existence vstupního souboru
    input_path = pathlib.Path(INPUT_MD_FILE)
    if not input_path.exists():
        print(f"❌ Chyba: Soubor {INPUT_MD_FILE} neexistuje!")
        print("Nejprve spusťte pdf_to_md.py pro vytvoření markdown souboru.")
        return
    
    # Vytvoř výstupní adresář
    output_path = pathlib.Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    
    # Načti markdown obsah
    print(f"Načítám {INPUT_MD_FILE}...")
    md_text = input_path.read_text(encoding='utf-8')
    print(f"Načteno: {len(md_text)} znaků")
    
    # Rozdělení na řádky a zpracování po řádkách
    lines = md_text.split('\n')
    
    chapters = []
    current_chapter_lines = []
    current_title = "ÚVOD"
    current_level = 1
    chapter_counter = 1
    
    print("Zpracovávám kapitoly...")
    
    for line in lines:
        title, level = extract_heading_info(line)
        
        if title and level:  # Našli jsme nadpis
            # Uložit předchozí kapitolu (pokud má obsah)
            if current_chapter_lines:
                filename, content = create_chapter_file(
                    current_chapter_lines, 
                    current_title, 
                    chapter_counter, 
                    current_level
                )
                chapters.append((filename, content))
                print(f"Kapitola {chapter_counter}: {current_title} (úroveň {current_level})")
                chapter_counter += 1
            
            # Začít novou kapitolu
            current_title = title
            current_level = level
            current_chapter_lines = []
            
        else:
            # Přidat řádek do aktuální kapitoly
            current_chapter_lines.append(line)
    
    # Uložit poslední kapitolu
    if current_chapter_lines:
        filename, content = create_chapter_file(
            current_chapter_lines, 
            current_title, 
            chapter_counter, 
            current_level
        )
        chapters.append((filename, content))
        print(f"Kapitola {chapter_counter}: {current_title} (úroveň {current_level})")
    
    # Pokud nebyl nalezen žádný nadpis, vytvoř jednu kapitolu "ÚVOD"
    if not chapters and lines:
        filename, content = create_chapter_file(
            lines, 
            "ÚVOD", 
            1, 
            1
        )
        chapters.append((filename, content))
        print("Nevytvořeny žádné kapitoly podle nadpisů, vytvořena kapitola ÚVOD")
    
    # Ulož všechny kapitoly
    print(f"\nUkládám {len(chapters)} kapitol...")
    
    for filename, content in chapters:
        file_path = output_path / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"Uloženo: {filename}")
    
    print(f"\n✅ Hotovo! Vytvořeno {len(chapters)} kapitol v {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()