import pathlib
import yaml
import re

CHAPTERS_DIR = "docs-site/docs/chapters"
INDEXES_DIR = "docs-site/docs/indexes"
MKDOCS_YML = "docs-site/mkdocs.yml"

labels_czech = {
    'address_number': 'Čísla popisná', 
    'event': 'Témata', 
    'name': 'Jména', 
    'year': 'Roky'
} # keep synced with md_split.py


def extract_frontmatter(md_file):
    """Extrahuje frontmatter z MD souboru"""
    content = md_file.read_text(encoding='utf-8')
    
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                return frontmatter
            except yaml.YAMLError:
                return {}
    return {}


def build_navigation():
    """Vytvoří hierarchickou navigaci podle heading_level"""
    chapters_path = pathlib.Path(CHAPTERS_DIR)
    
    # Najdi všechny chapter soubory
    chapter_files = sorted(chapters_path.glob("chapter_*.md"))
    
    chapters = []
    for file in chapter_files:
        frontmatter = extract_frontmatter(file)
        if frontmatter:
            chapters.append({
                'file': file.name,
                'title': frontmatter.get('title', file.stem),
                'level': frontmatter.get('heading_level', 1),
                'chapter_number': frontmatter.get('chapter_number', 999),
                'is_placeholder': frontmatter.get('is_placeholder', False)
            })
    
    # Seřaď podle chapter_number
    chapters.sort(key=lambda x: x['chapter_number'])
    
    # Vytvoř hierarchickou strukturu podle heading_level
    nav_structure = []
    current_parent = None
    
    for chapter in chapters:

        if type(chapter['level']) is not int:
            print(f"⚠️ Varování: Kapitola '{chapter['title']}' má neplatný heading_level '{chapter['level']}'.")

        if chapter['level'] <= 2:  # Úroveň 1 nebo 2 = hlavní sekce
            # Nová hlavní sekce
            section = {
                'title': chapter['title'],
                'file': chapter['file'],
                'is_placeholder': chapter['is_placeholder'],
                'children': []
            }
            nav_structure.append(section)
            current_parent = section
            
        else:  # Úroveň 3+ = podkapitoly
            # Přidej jako podkapitolu k poslední hlavní sekci
            if current_parent:
                current_parent['children'].append({
                    'title': chapter['title'],
                    'file': chapter['file'],
                    'is_placeholder': chapter['is_placeholder'],
                })
            else:
                # Fallback - pokud není parent, vytvoř jako hlavní sekci
                section = {
                    'title': chapter['title'],
                    'file': chapter['file'],
                    'is_placeholder': chapter['is_placeholder'],
                    'children': []
                }
                nav_structure.append(section)
                current_parent = section
    
    return nav_structure


def find_index_files():
    """Najde všechny index soubory"""
    indexes_path = pathlib.Path(INDEXES_DIR)
    if not indexes_path.exists():
        return []
    
    index_files = []
    for file in sorted(indexes_path.glob("*.md")):
        # Vytvoř pěkný název z názvu souboru
        name = file.stem
        title = labels_czech.get(name, name)

        index_files.append({
            'title': title,
            'file': f"indexes/{file.name}"
        })
    
    return index_files


def generate_nav_yaml(nav_structure):
    """Vygeneruje YAML strukturu pro MkDocs navigaci"""
    nav = []

    nav.append({"Úvod": "index.md"})
    
    for item in nav_structure:
        if item['children']:
            # Sekce s podkapitolami
            children_list = []
            
            # # Hlavní sekce jako první položka
            if not item['is_placeholder']:
                children_list.append({item['title']: f"chapters/{item['file']}"})
            
            # Pak všechny podkapitoly
            for child in item['children']:
                if not child['is_placeholder']:
                    children_list.append({child['title']: f"chapters/{child['file']}"})
            
            # Použij název hlavní sekce pro celou skupinu
            nav.append({item['title']: children_list})
            
        else:
            # Samostatná sekce bez podkapitol
            nav.append({item['title']: f"chapters/{item['file']}"})
    
    # Přidej sekci Indexy
    index_files = find_index_files()
    if index_files:
        indexes_section = []
        for index_file in index_files:
            indexes_section.append({index_file['title']: index_file['file']})
        
        nav.append({"Indexy": indexes_section})
    
    return nav


def update_mkdocs_yml(new_nav):
    """Aktualizuje mkdocs.yml s novou navigací"""
    mkdocs_path = pathlib.Path(MKDOCS_YML)
    
    if mkdocs_path.exists():
        # Načti existující konfiguraci
        with open(mkdocs_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # Aktualizuj navigaci
    config['nav'] = new_nav
    
    # Ulož zpět
    with open(mkdocs_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Navigace aktualizována v {MKDOCS_YML}")


def main():
    print("Generuji hierarchickou navigaci...")
    
    nav_structure = build_navigation()
    print(f"Nalezeno {len(nav_structure)} hlavních kapitol")
    
    new_nav = generate_nav_yaml(nav_structure)
    
    update_mkdocs_yml(new_nav)
    
if __name__ == "__main__":
    main()