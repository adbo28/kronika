import pathlib
import yaml
import re

CHAPTERS_DIR = "docs-site/docs"
MKDOCS_YML = "docs-site/mkdocs.yml"


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
                'chapter_number': frontmatter.get('chapter_number', 999)
            })
    
    # Seřaď podle chapter_number
    chapters.sort(key=lambda x: x['chapter_number'])
    
    # Vytvoř hierarchickou strukturu podle heading_level
    nav_structure = []
    current_parent = None
    
    for chapter in chapters:
        if chapter['level'] <= 2:  # Úroveň 1 nebo 2 = hlavní sekce
            # Nová hlavní sekce
            section = {
                'title': chapter['title'],
                'file': chapter['file'],
                'children': []
            }
            nav_structure.append(section)
            current_parent = section
            
        else:  # Úroveň 3+ = podkapitoly
            # Přidej jako podkapitolu k poslední hlavní sekci
            if current_parent:
                current_parent['children'].append({
                    'title': chapter['title'],
                    'file': chapter['file']
                })
            else:
                # Fallback - pokud není parent, vytvoř jako hlavní sekci
                section = {
                    'title': chapter['title'],
                    'file': chapter['file'],
                    'children': []
                }
                nav_structure.append(section)
                current_parent = section
    
    return nav_structure


def generate_nav_yaml(nav_structure):
    """Vygeneruje YAML strukturu pro MkDocs navigaci"""
    nav = []
    nav.append({"Úvod": "index.md"})
    
    for item in nav_structure:
        if item['children']:
            # Sekce s podkapitolami
            children_list = []
            
            # Hlavní sekce jako první položka
            children_list.append({item['title']: item['file']})
            
            # Pak všechny podkapitoly
            for child in item['children']:
                children_list.append({child['title']: child['file']})
            
            # Použij název hlavní sekce pro celou skupinu
            nav.append({item['title']: children_list})
            
        else:
            # Samostatná sekce bez podkapitol
            nav.append({item['title']: item['file']})
    
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
    
    # Debug: zobraz strukturu
    print("\nVygenerovaná navigace:")
    print(yaml.dump(new_nav, default_flow_style=False, allow_unicode=True))
    
    update_mkdocs_yml(new_nav)
    
    print("\nHotovo! Restartuj MkDocs server.")


if __name__ == "__main__":
    main()