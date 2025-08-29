import pathlib
import yaml
import re
import json
from collections import defaultdict
from typing import Dict, List

INPUT_MD_FILE = "./data/kronika_plus.md"
INDEX_DATA_FILE = "./data/index_data.jsonl"
OUTPUT_DIR = "./output/chapters"
INDEXES_DIR = "./output/indexes"
GLOBAL_INDEX_FILE = "./data/global_index.json"


def load_index_data() -> List[Dict]:
    """Načte index data z JSONL souboru"""
    index_path = pathlib.Path(INDEX_DATA_FILE)
    if not index_path.exists():
        print(f"❌ Chyba: Soubor {INDEX_DATA_FILE} neexistuje!")
        return []
    
    entities = []
    with open(INDEX_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entities.append(json.loads(line))
    
    print(f"Načteno {len(entities)} entit z indexu")
    return entities


def extract_heading_info(line):
    """Extrahuje informace o nadpisu z markdown řádky"""
    match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
    if match:
        hashes = match.group(1)
        title = match.group(2).strip()
        title = clean_title(title)
        level = len(hashes)
        return title, level
    return None, None


def clean_title(title):
    """Odstraní markdown formátování z názvu kapitoly"""
    title = re.sub(r'\*\*(.*?)\*\*', r'\1', title)
    title = re.sub(r'\*(.*?)\*', r'\1', title)
    title = title.strip()
    return title


def add_index_links_to_content(content: str, entities: List[Dict], chapter_num: int) -> str:
    """Přidá odkazy na indexy k existujícím anchor tagům. Kromě toho aktualizuje entity o číslo kapitoly."""
    # Seskup entity podle anchor_id pro rychlé vyhledávání
    anchor_to_entity = {entity['anchor_id']: entity for entity in entities}
    
    # Najdi všechny anchor tagy a obal je odkazy
    def replace_anchor(match):
        anchor_id = match.group(1)
        anchor_content = match.group(2)
        
        if anchor_id in anchor_to_entity:
            entity = anchor_to_entity[anchor_id]
            entity_type = entity['type'].lower()

            # Přidej číslo kapitoly do entity
            if 'chapters' not in entity:
                entity['chapters'] = [chapter_num]
            else:
                if chapter_num not in entity['chapters']:
                    entity['chapters'].append(chapter_num)

            index_link = f"/indexes/{entity_type}#{anchor_id}"
            return f' <a id="{anchor_id}" href="{index_link}">{anchor_content}</a> '
        else:
            print(f"[WARN] Anchor ID {anchor_id} nenalezen v indexu")   
            return match.group(0)  # Vrať původní, pokud entita nenalezena
    
    # Pattern pro anchor tagy: <a id="anchor-id">content</a>
    pattern = r'<a id="([^"]+)">([^<]+)</a>'
    return re.sub(pattern, replace_anchor, content)


def create_chapter_file(content_lines: List[str], title: str, chapter_num: int, level: int, entities: List[Dict]):
    """Vytvoří markdown soubor s YAML frontmatter"""
    frontmatter = {
        'title': title,
        'chapter_number': chapter_num,
        'heading_level': level,
        'nav_weight': chapter_num,
    }
    
    yaml_header = yaml.dump(frontmatter, 
                           allow_unicode=True, 
                           default_flow_style=False,
                           sort_keys=False)
    
    content = '\n'.join(content_lines)

    content = add_index_links_to_content(content, entities, chapter_num)
    
    full_content = f"---\n{yaml_header}---\n\n{content}"
    
    filename = f"chapter_{chapter_num:03d}.md"
    return filename, full_content


def create_index_files(entities: List[Dict], chapters_info: List[Dict]):
    """Vytvoří index soubory pro každý typ entity"""
    by_type = defaultdict(lambda: defaultdict(list))
    
    # Seskup entity podle typu a hodnoty
    for entity in entities:
        entity_type = entity['type']
        value = entity['value']
        by_type[entity_type][value].append(entity)
    
    # Vytvoř adresář pro indexy
    indexes_path = pathlib.Path(INDEXES_DIR)
    indexes_path.mkdir(parents=True, exist_ok=True)
    
    # Vytvoř index soubor pro každý typ
    for entity_type, values_dict in by_type.items():
        type_name = entity_type.lower()
        filename = f"{type_name}.md"
        
        sorted_values = sorted(values_dict.keys())
        
        content_lines = [
            f"# {entity_type.title()} Index",
            "",
            f"Celkem {len(sorted_values)} různých {type_name}.",
            ""
        ]
        
        for value in sorted_values:
            occurrences = values_dict[value]
            anchor_id = occurrences[0]['anchor_id']  # Použij anchor_id z entity dat
            
            content_lines.append(f"<a id='{anchor_id}'></a>")
            content_lines.append(f"## {value}")            
            # content_lines.append(f"## {value}")
            content_lines.append("")
            content_lines.append(f"Nalezeno {len(occurrences)}x:")
            content_lines.append("")
            
            # Najdi kapitoly pro každý výskyt
            occurrence_chapters = set()
            for occurrence in occurrences:
                if 'chapters' in occurrence and occurrence['chapters']:
                    occurrence_chapters.update(occurrence['chapters'])

            # Přidej odkazy na kapitoly
            for chapter_num in sorted(occurrence_chapters):
                chapter_info = next(ch for ch in chapters_info if ch['number'] == chapter_num)
                chapter_title = re.sub(r'<[^>]+>', '', chapter_info['title']) # strip html tags
                link = f"- [Kapitola {chapter_num}: {chapter_title}](../chapters/chapter_{chapter_num:03d}.md#{anchor_id})"
                content_lines.append(link)
            
            content_lines.append("")
        
        # Uložit soubor
        index_file_path = indexes_path / filename
        index_file_path.write_text('\n'.join(content_lines), encoding='utf-8')
        print(f"Vytvořen index: {filename}")


def create_global_index(entities: List[Dict], chapters_info: List[Dict]):
    """Vytvoří globální JSON index"""
    by_type = defaultdict(lambda: defaultdict(list))
    
    for entity in entities:
        entity_type = entity['type']
        value = entity['value']
        by_type[entity_type][value].append(entity)
    
    global_index = {
        "metadata": {
            "total_entities": len(entities),
            "chapters_count": len(chapters_info),
            "entity_types": {entity_type: len(values_dict) 
                           for entity_type, values_dict in by_type.items()}
        },
        "entities": {}
    }
    
    # Zpracuj každý typ
    for entity_type, values_dict in by_type.items():
        global_index["entities"][entity_type] = {}
        
        for value, occurrences in values_dict.items():
            global_index["entities"][entity_type][value] = {
                "total_count": len(occurrences),
                "anchor_id": occurrences[0]['anchor_id'],
                "full_matches": list(set([occ.get('full_match', value) for occ in occurrences])), # TODO potřebujeme to vůbec?
                "chapters": list({ch for occ in occurrences for ch in occ.get('chapters', []) if occ.get('chapters')}),
                "contexts": [occ.get('context', '') for occ in occurrences if occ.get('context')]
            }
    
    # Ulož globální index
    pathlib.Path(GLOBAL_INDEX_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(global_index, f, ensure_ascii=False, indent=2)
    
    print(f"Vytvořen globální index: {GLOBAL_INDEX_FILE}")


def main():
    # Načti index data
    entities = load_index_data()
    if not entities:
        return
    
    # Kontrola existence vstupního souboru
    input_path = pathlib.Path(INPUT_MD_FILE)
    if not input_path.exists():
        print(f"❌ Chyba: Soubor {INPUT_MD_FILE} neexistuje!")
        return
    
    # Vytvoř výstupní adresář
    output_path = pathlib.Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Načti markdown obsah
    print(f"Načítám {INPUT_MD_FILE}...")
    md_text = input_path.read_text(encoding='utf-8')
    print(f"Načteno: {len(md_text)} znaků")
    
    lines = md_text.split('\n')
    
    chapters = []
    chapters_info = []
    current_chapter_lines = []
    current_title = "ÚVOD"
    current_level = 1
    chapter_counter = 1
    
    print("Zpracovávám kapitoly...")
    
    for _, line in enumerate(lines):
        title, level = extract_heading_info(line)
        
        if title and level:  # Našli jsme nadpis
            # Uložit předchozí kapitolu (pokud má obsah)
            if current_chapter_lines:
                filename, content = create_chapter_file(
                    current_chapter_lines, 
                    current_title, 
                    chapter_counter, 
                    current_level,
                    entities
                )
                chapters.append((filename, content))
                
                chapters_info.append({
                    'number': chapter_counter,
                    'title': current_title,
                    'level': current_level
                })
                
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
            current_level,
            entities
        )
        chapters.append((filename, content))
        
        chapters_info.append({
            'number': chapter_counter,
            'title': current_title,
            'level': current_level
        })
        
        print(f"Kapitola {chapter_counter}: {current_title} (úroveň {current_level})")
    
    # Pokud nebyl nalezen žádný nadpis, vytvoř jednu kapitolu
    if not chapters and lines:
        filename, content = create_chapter_file(lines, "ÚVOD", 1, 1)
        chapters.append((filename, content))
        chapters_info.append({'number': 1, 'title': 'ÚVOD', 'level': 1})
        print("Vytvořena kapitola ÚVOD")
    
    # Ulož všechny kapitoly
    print(f"\nUkládám {len(chapters)} kapitol...")
    for filename, content in chapters:
        file_path = output_path / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"Uloženo: {filename}")
    
    # Vytvoř indexy
    print(f"\nVytvářím indexy...")
    create_index_files(entities, chapters_info)
    create_global_index(entities, chapters_info)
    
    print(f"\n✅ Hotovo! Vytvořeno {len(chapters)} kapitol v {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()