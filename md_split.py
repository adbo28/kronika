import pathlib
import yaml
import re
import json
from collections import defaultdict
from typing import Dict, List, Optional

INPUT_MD_FILE = "./data/kronika_plus.md"
INDEX_DATA_FILE = "./data/index_data.jsonl"
STRUCTURE_CONFIG_FILE = "./data/chapter_mapping.jsonl"
OUTPUT_DIR = "./output/chapters"
INDEXES_DIR = "./output/indexes"
GLOBAL_INDEX_FILE = "./data/global_index.json"

labels_czech = {
    'address_number': 'Čísla popisná', 
    'event': 'Klíčová slova', 
    'name': 'Jména', 
    'year': 'Roky'
} # keep synced with generate_nav.py


def load_structure_mapping(jsonl_file: str) -> List[Dict]:
    """Load structure mapping from JSONL file"""
    config_path = pathlib.Path(jsonl_file)
    if not config_path.exists():
        print(f"❌ Chyba: Konfigurační soubor {jsonl_file} neexistuje!")
        return []
    
    mappings = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    mapping = json.loads(line)
                    mappings.append(mapping)
                except json.JSONDecodeError as e:
                    print(f"❌ Chyba na řádku {line_num}: {e}")
                    return []
    
    print(f"Načteno {len(mappings)} konfigurací z {jsonl_file}")
    return mappings


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


def parse_all_sections(md_text: str) -> Dict[str, Dict]:
    """Parse all sections from markdown and return indexed by title"""
    lines = md_text.split('\n')
    sections = {}
    current_title = None
    current_level = None
    current_content = []
    
    for line in lines:
        title, level = extract_heading_info(line)
        
        if title and level:  # Found a heading
            # Save previous section
            if current_title is not None:
                count = len([s for s in sections.keys() if s == current_title])
                if count > 0:
                    current_title = f"{current_title}_{count+1}"

                sections[current_title] = {
                    'level': current_level,
                    'content': current_content.copy(),
                    'found': False  # Track if this section was used
                }
            
            # Start new section
            current_title = title
            current_level = level
            current_content = []
        else:
            # Add line to current section content
            current_content.append(line)
    
    # Save last section
    if current_title is not None:
        sections[current_title] = {
            'level': current_level,
            'content': current_content.copy(),
            'found': False
        }
    
    print(f"Nalezeno {len(sections)} původních sekcí")
    return sections


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

            index_link = f"/kronika/indexes/{entity_type}#{anchor_id}"

            return f' <a id="{anchor_id}" href="{index_link}">{anchor_content}</a> '
        else:
            print(f"[WARN] Anchor ID {anchor_id} nenalezen v indexu")   
            return match.group(0)  # Vrať původní, pokud entita nenalezena
    
    # Pattern pro anchor tagy: <a id="anchor-id">content</a>
    pattern = r'<a id="([^"]+)">([^<]+)</a>'
    return re.sub(pattern, replace_anchor, content)


def create_chapter_file(content_lines: List[str], title: str, chapter_num: int, level: int, entities: List[Dict]):
    """Vytvoří markdown soubor s YAML frontmatter"""

    is_placeholder = not content_lines or all(line.strip() == "" for line in content_lines)

    frontmatter = {
        'title': title,
        'chapter_number': chapter_num,
        'heading_level': level,
        'nav_weight': chapter_num,
        'is_placeholder': is_placeholder,
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
        
        czech_label = labels_czech.get(entity_type.lower(), entity_type.title())
        print(f"Vytvářím index pro {czech_label}[{entity_type.title()}] ({len(sorted_values)} položek)")
        content_lines = [
            f"# {czech_label}",
            "",
            f"Celkem {len(sorted_values)} různých položek.",
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
            chapters_list = list({ch for occ in occurrences for ch in occ.get('chapters', []) if occ.get('chapters')})
            contexts_list = [occ.get('context', '') for occ in occurrences if occ.get('context')]
            if not chapters_list and contexts_list:
                print(f"❌ ERROR: Entity '{value}' in type '{entity_type}' has empty chapters but {len(contexts_list)} contexts")
            global_index["entities"][entity_type][value] = {
                "total_count": len(occurrences),
                "anchor_id": occurrences[0]['anchor_id'],
                "full_matches": list(set([occ.get('full_match', value) for occ in occurrences])), # TODO potřebujeme to vůbec?
                "chapters": chapters_list,
                "contexts": contexts_list
            }
    
    # Ulož globální index
    pathlib.Path(GLOBAL_INDEX_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(global_index, f, ensure_ascii=False, indent=2)
    
    print(f"Vytvořen globální index: {GLOBAL_INDEX_FILE}")


def process_with_configuration(original_sections: Dict[str, Dict], 
                             structure_mappings: List[Dict], 
                             entities: List[Dict]) -> List[tuple]:
    """Process sections according to configuration"""
    chapters = []
    chapters_info = []
    chapter_counter = 1
    current_content_buffer = []
    current_title = None
    current_level = None
    
    def save_current_chapter():
        nonlocal chapter_counter, current_content_buffer, current_title, current_level
        if current_title and current_level is not None:
            filename, content = create_chapter_file(
                current_content_buffer, current_title, chapter_counter, 
                current_level, entities
            )
            chapters.append((filename, content))
            chapters_info.append({
                'number': chapter_counter,
                'title': current_title,
                'level': current_level
            })
            # print(f"Kapitola {chapter_counter}: {current_title} (úroveň {current_level})")
            chapter_counter += 1
            current_content_buffer = []
            current_title = None
            current_level = None
        else:
            if current_content_buffer:
                print(f"❌ CHYBA: Nelze uložit kapitolu bez názvu nebo úrovně! Titulek: {current_title}")
    
    print("Zpracovávám podle konfigurace...")
    
    for mapping in structure_mappings:
        original_title = mapping.get('original_title')
        new_title = mapping.get('new_title')
        new_level = mapping.get('new_level')
        
        if original_title:  # Existing section to map
            if original_title in original_sections:
                section = original_sections[original_title]
                section['found'] = True  # Mark as used
                
                if new_title and new_level is not None:
                    # Save any previous chapter first
                    save_current_chapter()
                    
                    # Start new chapter
                    current_title = new_title
                    current_level = new_level
                    current_content_buffer = section['content'].copy()
                
                elif new_title is None:
                    # Append to current buffer (consolidation)
                    if section['content']:
                        if current_content_buffer:
                            current_content_buffer.append("")
                            current_content_buffer.append("---")  
                            current_content_buffer.append("")
                        
                        # Add original title as level 4 heading
                        current_content_buffer.append(f"#### {original_title}")
                        current_content_buffer.append("")
                        current_content_buffer.extend(section['content'])

                else:
                    print(f"❌ CHYBA: Neplatná kombinace pro '{original_title}': new_title={new_title}, new_level={new_level}")
            else:
                print(f"❌ CHYBA: Původní sekce '{original_title}' nebyla nalezena!")
                
        elif new_title and new_level is not None:  # New section to insert
            # Save any previous chapter first
            save_current_chapter()
            
            # Start new section (initially empty)
            current_title = new_title
            current_level = new_level
            current_content_buffer = []
        else:
            print(f"❌ CHYBA: Neplatné mapování: original_title={original_title}, new_title={new_title}, new_level={new_level}")
    
    # Save final buffered content
    save_current_chapter()
    
    return chapters, chapters_info


def validate_all_content_used(original_sections: Dict[str, Dict]):
    """Check that all original sections were used"""
    unused_sections = [title for title, section in original_sections.items()
                      if not section['found']]

    if unused_sections:
        print(f"\n❌ ERROR: The following {len(unused_sections)} original sections were not used and will be dropped:")
        for title in unused_sections:
            level = original_sections[title]['level']
            suggested_mapping = f'{{"original_title": "{title}", "new_title": "TODO", "new_level": "TODO"}}'
            print(f"   [Level {level}] {title}")
            print(f"   Suggested mapping to add to chapter_mapping.jsonl: {suggested_mapping}")
        print("\nThese sections will be lost! Add the suggested mappings to the configuration file.")
    else:
        print(f"✅✅ Všechny {len(original_sections)} původní sekce byly použity")

    return True


def main():
    # Load configuration
    structure_mappings = load_structure_mapping(STRUCTURE_CONFIG_FILE)
    if not structure_mappings:
        return
    
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
    
    # Parse all original sections
    original_sections = parse_all_sections(md_text)
    
    # Process according to configuration
    chapters, chapters_info = process_with_configuration(
        original_sections, structure_mappings, entities
    )
    
    # Validate all content was used
    if not validate_all_content_used(original_sections):
        return
    
    # Ulož všechny kapitoly
    print(f"\nUkládám {len(chapters)} kapitol...")
    for filename, content in chapters:
        file_path = output_path / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"Uloženo: {filename}", end=', ')
    
    # Vytvoř indexy
    print(f"\nVytvářím indexy...")
    create_index_files(entities, chapters_info)
    create_global_index(entities, chapters_info)
    
    print(f"\n✅ Hotovo! Vytvořeno {len(chapters)} kapitol v {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()