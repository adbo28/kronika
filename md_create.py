import pathlib
import pymupdf4llm
import re

INPUT_FILE = "..\\inputs\\Kronika-Stara-Ves-1923-1991-epdf.pdf"
MAIN_OUTPUT_FILE = "./data/kronika.md"


def fix_soft_hyphens(text):
    """Odstraní soft hyphens (U+00AD) a spojí rozdělená slova"""
    # Soft hyphen následovaný whitespace/newline - spojit slova
    text = re.sub(r'­\s+', '', text)
    return text


def fix_page_breaks(text):
    """Spojí text přes page breaks pokud je to bezpečné"""
    lines = text.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        current_line = lines[i].strip()
        
        # Pokud není další řádek, prostě přidej aktuální
        if i + 1 >= len(lines):
            fixed_lines.append(lines[i])
            i += 1
            continue
            
        next_line = lines[i + 1].strip()
        
        # Podmínky pro BEZPEČNÉ spojení:
        # 1. Aktuální řádek nekončí větnou tečkou (., !, ?)
        # 2. Aktuální řádek není prázdný
        # 3. Následující řádek není nadpis (nezačína #)
        # 4. Následující řádek začína malým písmenem (pokračování věty)
        # 5. Následující řádek není prázdný
        
        should_join = (
            current_line and  # aktuální řádek není prázdný
            not re.search(r'[.!?]\s*$', current_line) and  # nekončí větnou tečkou
            next_line and  # následující řádek není prázdný
            not next_line.startswith('#') and  # není nadpis
            next_line[0].islower()  # začína malým písmenem
        )
        
        if should_join:
            # Spoj řádky s mezerou
            combined_line = current_line + ' ' + next_line
            fixed_lines.append(combined_line)
            i += 2  # přeskoč následující řádek (už je spojen)
        else:
            fixed_lines.append(lines[i])
            i += 1
    
    return '\n'.join(fixed_lines)


def main():
    # Převeď PDF na markdown (bez page_chunks)
    print("Převádím PDF na markdown...")
    md_text = pymupdf4llm.to_markdown(
        INPUT_FILE,
        # pages=[0,1,2,3,4,5,6],  # pro testování
        margins=[1, 1, 1, 50.0],
        page_chunks=False,  # Chceme jeden velký text
        ignore_images=True,
        show_progress=True,
    )
    
    print("Opravujem soft hyphens...")
    md_text = fix_soft_hyphens(md_text)
    
    print("Opravujem page breaks...")
    md_text = fix_page_breaks(md_text)
    
    # ulož hlavní výstupní soubor
    pathlib.Path(MAIN_OUTPUT_FILE).write_bytes(md_text.encode())        

    print(f"✅ Převedeno a opraveno! Celková délka: {len(md_text)} znaků")
    print(f"Výstupní soubor: {MAIN_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
