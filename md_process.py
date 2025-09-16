import json
import re
import hashlib
import pathlib
from typing import List, Tuple, Dict, Optional, Any, Set


# Configuration
INPUT_MD_FILE = "./data/kronika.md"
FILE_ENRICHED = "./data/kronika_plus.md"
OUTPUT_FILE = "./data/index_data.jsonl"

MAX_WINDOW_SIZE = 5 # kolik slov může mít jedna entita

CONTEXT_SIZE_BLOCKS = 10 # počet bloků před a za entitou pro kontext

###########################################################


def get_base_forms(file_path):
   """
   Read a JSONL file and return a dictionary mapping original_name to base_form.
   """
   result = {}
   
   with open(file_path, 'r', encoding='utf-8') as file:
       for line in file:
           line = line.strip()
           if line:  # Skip empty lines
               data = json.loads(line)
               result[data['original_name']] = data['base_form']
   
   return result

# Načti základní formy jmen z externího souboru
event_base_forms = get_base_forms('./data/event_base_form.jsonl')
name_base_forms = get_base_forms('./data/name_base_form.jsonl')

def check_event_match(text_sequence: str) -> Optional[Tuple[str, str, str]]:
    """
    Kontrola, zda textová sekvence odpovídá nějaké události.
    Vrací název události nebo None.
    """
    
    # Zkontroluj case-insensitive match
    base = event_base_forms.get(text_sequence.lower())
    if base:
        return("EVENT", base, text_sequence)
    
    return None

# ---------------------------------------------------------

def load_word_list(filename: str) -> Set[str]:
    """Načte seznam slov ze souboru (jedno slovo na řádek)"""
    with open(filename, 'r', encoding='utf-8') as f:
        return {line.strip().lower() for line in f if line.strip()}

names_with_dots = load_word_list('./data/names_with_dots.txt')
first_names = load_word_list('./data/first_names.txt')


def check_name_match(text_sequence: str) -> Optional[Tuple[str, str, str]]:
    """
    Kontrola, zda textová sekvence odpovídá nějakému jménu.
    Vrací tuple ("NAME", base_form, původní_text) nebo None.
    """
    
    if not text_sequence:
        return None

    # Rozdělí na slova
    words = text_sequence.split()
    
    if len(words) < 2: # jméno musí mít alespoň 2 slova
        return None

    for i, word in enumerate(words):
        # Odstranění trailing interpunkce z posledního slova
        clean_word = word
        if i == len(words) - 1:  # poslední slovo
            # Odstraň trailing interpunkci definovanou v TRAILING_PUNCT
            clean_word = re.sub(TRAILING_PUNCT + r'$', '', word)
        
        # Kontrola formátu slova: začíná velkým písmenem, zbytek malá písmena
        if not clean_word:
            return None            
        if not clean_word[0].isupper():
            return None
        if not clean_word[1:].islower():
            return None
        
        # Kontrola, že obsahuje pouze písmena (+ případně tečku na konci)
        base_letters = clean_word.rstrip('.')
        if not re.match(r'^[A-Za-záčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽäöüÄÖÜ]+$', base_letters):
            return None

        # Kontrola tečky u ne-posledních slov
        if i < len(words) - 1:
            if word.endswith('.'):
                # Ne-poslední slovo končí tečkou - musí být v seznamu povolených
                if clean_word.lower() not in names_with_dots:
                    return None
            else:
                # Ne-poslední slovo bez tečky - musí být v seznamu first_names
                if clean_word.lower() not in first_names:
                    return None

    # Validace: alespoň jedno slovo > 2 znaky
    if not any(len(word) > 2 for word in words):
        return None

    # Získat base form (nebo ponechat původní)
    clean_text = re.sub(TRAILING_PUNCT + r'$', '', text_sequence)
    base_form = name_base_forms.get(clean_text, clean_text)

    # Kontrola, že base_form má alespoň 2 slova
    if len(base_form.split()) < 2:
        return None

    return ("NAME", base_form, text_sequence)


# ---------------------------------------------------------

TRAILING_PUNCT = r'[.,;:)\]_]*'   # allow multiple, e.g. ")." or ")_" etc.


def has_address_prefix(blocks: List[Tuple[str, Any]], i_start: int) -> bool:
    """
    Scan backwards from i_start and check whether the first non-whitespace,
    non-number, non-connector block is a valid address prefix ("č", "č.", "c", "c.").
    """
    j = i_start - 1
    while j >= 0:
        prev_text, block_type = blocks[j]
        text = prev_text.strip()

        if block_type == BLOCK_TYPE_WHITESPACE or not text:
            j -= 1
            continue

        # skip numbers with optional punctuation (e.g. "7,", "8")
        if re.fullmatch(r'\d{1,4}[,]?', text):
            j -= 1
            continue

        # skip the connector "a"
        if text.lower() == "a":
            j -= 1
            continue

        # check for prefix
        if re.fullmatch(r'[cčCČ]\.?', text):
            return True

        # any other content means no valid prefix
        return False

    return False


def check_address_numbers(
    text_sequence: str,
    blocks: List[Tuple[str, Any]],
    i_start: int,
    i_end: int
) -> Optional[Tuple[str, str, str]]:
    """
    Ověří, zda sekvence bloků [i_start:i_end] představuje validní adresní číslo.
    Rozpozná pouze čísla, která jsou součástí sekvence za prefixem "č.", "č", "c.", "c.".
    """

    # číslo musí být samotné 1–4 číslice, volitelně s čárkou nebo tečkou nebo závorkou na konci
    if not re.fullmatch(rf'\d{{1,4}}{TRAILING_PUNCT}?$', text_sequence):
        return None

    # kontrola prefixu
    if not has_address_prefix(blocks, i_start):
        return None

    cur_num = re.findall(r'\d+', text_sequence)[0]

    # kontrola rozsahu 1-299
    if not (0 < int(cur_num) < 300):
        return None

    return ("ADDRESS_NUMBER", cur_num, text_sequence)


# ---------------------------------------------------------

def check_years(
    text_sequence: str,
    blocks: List[Tuple[str, Any]],
    i_start: int,
    i_end: int
) -> Optional[Tuple[str, str, str]]:
    """
    Ověří, zda sekvence bloků [i_start:i_end] představuje validní rok.
    Vrací tuple ("YEAR", rok_jako_string, původní_text_bloku) nebo None.
    """

    # jednotky zakazující interpretaci čísla jako rok
    unit_after = r'(?:kg|Kčs?|K|zl|osob|l|sáh(?:u|ů|y)?|obyvatel(?:ů|é|e)?|m|km|a|ha|kop|%|str|stran)'

    # --- Pattern 1: samostatné roky 3–4 číslice (s volitelnou koncovou interpunkcí) ---
    m1 = re.fullmatch(rf'(\d{{3,4}}){TRAILING_PUNCT}', text_sequence)
    if m1:
        year = int(m1.group(1))
        if 500 <= year <= 2000:
            # --- kontrola fragmentace ---
            if i_start > 0:
                prev_text, block_type = blocks[i_start - 1]
                if block_type != BLOCK_TYPE_WHITESPACE and prev_text and prev_text[-1].isdigit():
                    return None
            if i_end + 1 < len(blocks):
                next_text, block_type = blocks[i_end + 1]
                if block_type != BLOCK_TYPE_WHITESPACE and re.match(r'^\d{3}\b', next_text):
                    return None

            # --- kontrola zakázaných jednotek za číslem ---
            if not re.search(r'[.,;:)\]_]$', text_sequence):  # skip unit-check if ended by punct
                j = i_end + 1
                while j < len(blocks):
                    block_text, block_type = blocks[j]
                    if block_type == BLOCK_TYPE_WHITESPACE:
                        j += 1
                        continue
                    # jednotka s volitelnou interpunkcí za ní
                    if re.match(rf'^{unit_after}{TRAILING_PUNCT}$', block_text, flags=re.IGNORECASE):
                        return None
                    break  # stop after first content block

            return ("YEAR", str(year), text_sequence)

    # --- Pattern 2: speciální formát "14 [16/6] 68" -> 1468 ---
    m2 = re.fullmatch(r'(\d{2})\s\[\s\d{1,2}\s/\s\d{1,2}\s\]\s(\d{2})', text_sequence)
    if m2:
        full_year = int(m2.group(1) + m2.group(2))
        if 500 <= full_year <= 2000:
            return ("YEAR", str(full_year), text_sequence)

    return None


###########################################################

def create_slug(text: str) -> str:
    """Vytvoří URL-friendly slug z textu s hash suffixem proti kolizím"""
    # Spočítej hash z původního textu
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:6]
    
    # Převeď na malá písmena a nahraď mezery pomlčkami
    slug = text.lower().replace(' ', '-')
    # Odstraň speciální znaky kromě pomlček a písmen
    slug = re.sub(r'[^\w\-]', '', slug)
    
    # Přidej hash suffix
    return f"{slug}-{text_hash}"


###########################################################

BLOCK_TYPE_WHITESPACE = 1
BLOCK_TYPE_CONTENT = 2
BLOCK_TYPE_TITLE = 3

def tokenize_to_blocks(text: str) -> List[Tuple[str, int]]:
    """
    Rozdělí text na bloky - střídavě whitespace, content a title bloky.
    Title blok začína novým řádkem následovaným volitelným whitespace a #.
    Vrací seznam tupelů (block_text, block_type)
    block_type: "whitespace", "content", "title"
    """
    blocks = []
    i = 0
    title_line_active = False
    current_block_start = 0
    current_block_type = None
    
    while i < len(text):
        if text[i] == '\n':
            # Save current block if we have one
            if current_block_type is not None and i > current_block_start:
                blocks.append((text[current_block_start:i], current_block_type))
            
            # Check if next line starts with title pattern (optional whitespace + #)
            peek_pos = i + 1
            while peek_pos < len(text) and text[peek_pos] in ' \t':
                peek_pos += 1
            
            if peek_pos < len(text) and text[peek_pos] == '#':
                # Next line is title
                title_line_active = True
                current_block_start = i + 1  # Start after newline
                current_block_type = BLOCK_TYPE_TITLE
            else:
                # Next line is not title
                title_line_active = False
                current_block_start = i
                current_block_type = BLOCK_TYPE_WHITESPACE  # Newline starts as whitespace
            
            i += 1
            
        elif title_line_active:
            # In title mode - just advance, everything goes into title block
            i += 1
            
        else:
            # Normal whitespace/content processing
            if text[i].isspace():
                # If we're not in whitespace block, save current and start whitespace
                if current_block_type != BLOCK_TYPE_WHITESPACE:
                    if current_block_type is not None and i > current_block_start:
                        blocks.append((text[current_block_start:i], current_block_type))
                    current_block_start = i
                    current_block_type = BLOCK_TYPE_WHITESPACE
                i += 1
            else:
                # If we're not in content block, save current and start content
                if current_block_type != BLOCK_TYPE_CONTENT:
                    if current_block_type is not None and i > current_block_start:
                        blocks.append((text[current_block_start:i], current_block_type))
                    current_block_start = i
                    current_block_type = BLOCK_TYPE_CONTENT
                i += 1
    
    # Save final block if we have one
    if current_block_type is not None and i > current_block_start:
        blocks.append((text[current_block_start:i], current_block_type))
    
    return blocks



def is_boundary(block: str, is_whitespace: bool) -> bool:
    """
    Detekuje konec odstavce/kapitoly pro reset sliding window.
    Paragraph: double newlines
    Chapter: # headers (markdown)
    """
    if not is_whitespace:
        # Check for markdown headers
        return block.startswith('#')
    else:
        # Check for paragraph break (double newlines)
        return '\n\n' in block
    
    return False


BW_LIST_FILE = './data/bw_list.jsonl'

def load_bw_list():
    """Load the blacklist/whitelist from JSONL file into global variable"""
    bw_list = {}
    with open(BW_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                bw_list[entry['value']] = entry

    return bw_list


# Global variable to store the blacklist/whitelist
BW_LIST = load_bw_list()


def check_entity_match(content_blocks: List[str], 
                       window_size: int, 
                       blocks: List[Tuple[str, Any]],
                       i_start: int,
                       i_end: int) -> Optional[Tuple[str, str, str]]:
    """
    Zkontroluje, jestli sekvence content_blocks odpovídá nějaké entitě.
    Vrací (pattern_type, value, full_match) nebo None
    """

    if window_size == 0:
        return None
        
    # Spojit bloky pro analýzu
    text_sequence = ' '.join(content_blocks[:window_size])

    # Kontrola proti blacklist/whitelist
    if text_sequence in BW_LIST:
        entry = BW_LIST[text_sequence]
        if not entry['valid']:
            return None
        return (entry['type'], entry.get('base_form', entry['value']), text_sequence)

    # Standardní kontroly na entity
    match = check_event_match(text_sequence)
    if not match:
        match = check_years(text_sequence, blocks, i_start, i_end)
    if not match:
        match = check_name_match(text_sequence)
    if not match:
        match = check_address_numbers(text_sequence, blocks, i_start, i_end)
    if not match:
        return None

    # Kontrola proti blacklist/whitelist pro případy, kdy value neodpovídá text_seq 
    # (například text_seq = "St. Vsi:" a value je "ST. Vsi")
    pattern_type, value, full_match = match
    if value != text_sequence:
        if value in BW_LIST:
            entry = BW_LIST[value]
            if not entry['valid']:
                return None
            return (entry['type'], entry.get('base_form', entry['value']), text_sequence)

    return (pattern_type, value, full_match)


def fill_content_window(blocks: List[Tuple[str, int]], start_pos: int, max_size: int) -> Tuple[List[str], List[int]]:
    """
    Pokud je na start_pos whitespace blok, vrátí jen tento jediný blok.
    Pokud je na start_pos title blok, vrátí jen tento jediný blok.
    Pokud je na start_pos content blok, naplní content_window od start_pos dopředu až do max_size content bloků.
    Zastaví se na boundary nebo konci bloků.
    Vrací (content_window, content_positions)
    """
    content_window = []
    content_positions = []
    
    if blocks[start_pos][1] == BLOCK_TYPE_WHITESPACE:
        # Whitespace blok - vrať jen tento jeden blok
        return [blocks[start_pos][0]], [start_pos]
    
    if blocks[start_pos][1] == BLOCK_TYPE_TITLE:
        # Title blok - vrať jen tento jeden blok
        return [blocks[start_pos][0]], [start_pos]

    pos = start_pos
    while pos < len(blocks) and len(content_window) < max_size:
        block_text, block_type = blocks[pos]
        
        if block_type == BLOCK_TYPE_WHITESPACE:
            # Zkontroluj boundary - pokud ano, zastav plnění
            if is_boundary(block_text, True):
                break
        elif block_type == BLOCK_TYPE_TITLE:
            # Title blok - zastav plnění (nepřekračuj title boundaries)
            break
        else:  # block_type == BLOCK_TYPE_CONTENT
            content_window.append(block_text)
            content_positions.append(pos)
            
            # Zkontroluj boundary - pokud ano, zastav plnění
            if is_boundary(block_text, False):
                break
                
        pos += 1
    
    return content_window, content_positions


    
def process_document(text: str) -> Tuple[str, List[Dict]]:
    """
    Hlavní funkce pro zpracování dokumentu.
    Vrací (enriched_text, entities_list)
    """
    blocks = tokenize_to_blocks(text)
    enriched_blocks = []
    entities = []

    i = 0
    while i < len(blocks):
        # Naplň plovoucí okno od pozice i
        content_window, content_positions = fill_content_window(blocks, i, MAX_WINDOW_SIZE)

        # Pokud okno neobsahuje žádné content bloky, pokračuj na další blok
        if not content_window:
            if len(enriched_blocks) <= i:
                enriched_blocks.append(blocks[i][0])
            i += 1
            continue

        # Zkus najít match - od nejdelší sekvence
        match_found = False
        for window_size in range(len(content_window), 0, -1):
            # vždy použít přesné start/end indexy z content_positions
            start_pos = content_positions[0]
            end_pos = content_positions[window_size - 1]

            match_result = check_entity_match(
                content_window,
                window_size,
                blocks,
                start_pos,
                end_pos
            )

            if match_result:
                pattern_type, value, full_match = match_result

                # Vytvoř anchor ID
                anchor_id = create_slug(value)

                # Přidej bloky mezi posledním zpracovaným a začátkem match
                for j in range(len(enriched_blocks), start_pos):
                    enriched_blocks.append(blocks[j][0])

                # Wrap matchované bloky do anchoru
                enriched_blocks.append(f'<a id="{anchor_id}">')
                for j in range(start_pos, end_pos + 1):
                    enriched_blocks.append(blocks[j][0])
                enriched_blocks.append('</a>')

                # Připrav kontext (před a za entitou)
                context_start = max(0, start_pos - CONTEXT_SIZE_BLOCKS)
                context_end = min(len(blocks) - 1, end_pos + CONTEXT_SIZE_BLOCKS)
                context = ''.join([b[0] for b in blocks[context_start:context_end]]).strip()

                # Zaznamenej entitu
                entity = {
                    "type": pattern_type,
                    "value": value,
                    "anchor_id": anchor_id,
                    "full_match": full_match,
                    "context": context  # Kontext není potřeba podle požadavků
                }
                entities.append(entity)

                # Pokračuj za matchem (žádný blok se nepřekrývá)
                i = end_pos + 1
                match_found = True
                break

        if not match_found:
            # Žádný match - zkopíruj první blok z okna a pokračuj
            enriched_blocks.append(blocks[i][0])
            i += 1

    return ''.join(enriched_blocks), entities


def main():
    # Kontrola existence vstupního souboru
    input_path = pathlib.Path(INPUT_MD_FILE)
    if not input_path.exists():
        print(f"❌ Chyba: Soubor {INPUT_MD_FILE} neexistuje!")
        return
    
    print(f"Načítám {INPUT_MD_FILE}...")
    text = input_path.read_text(encoding='utf-8')
    print(f"Načteno: {len(text)} znaků")
    
    print("Zpracovávám dokument...")
    enriched_text, entities = process_document(text)
    
    # Ulož obohacený dokument
    enriched_path = pathlib.Path(FILE_ENRICHED)
    enriched_path.write_text(enriched_text, encoding='utf-8')
    
    # Ulož entity do JSONL
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entity in entities:
            f.write(json.dumps(entity, ensure_ascii=False) + '\n')
    
    print(f"✅ Hotovo! Nalezeno {len(entities)} entit")
    print(f"Obohacený dokument: {FILE_ENRICHED}")
    print(f"Index entit: {OUTPUT_FILE}")
    
    # Zobraz statistiky
    if entities:
        print("\nStatistiky:")
        type_counts = {}
        for entity in entities:
            entity_type = entity['type']
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        for entity_type, count in type_counts.items():
            print(f"  {entity_type}: {count}")


if __name__ == "__main__":
    main()
