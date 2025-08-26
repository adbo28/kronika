import pathlib, re, json, csv
from dataclasses import dataclass
from typing import List, Tuple

INPUT_MD_FILE = "./data/kronika.md"
OUTPUT_FILE = "./data/index_data.jsonl"
RULES_FILE = "./data/pattern_rules.csv"
CONTEXT_LENGTH = 50

# Blacklist pro názvy (jen jednoslovné výrazy)
NAME_BLACKLIST = set(['dne', 'ten', 'státní', 'když', 'rok', 'první', 'jeho', 'byl', 'tak', 'potom', 'při', 'toho', 'kčs', 'také', 'zemřel', \
                      'vysokém', 'staré', 'vsi', 'vysokého', 'semil', 'praze', 'semilech', 'jilemnici', 'jilemnice', 'ale', 'stanového', 'vrchy', \
                      'bylo', 'roztokách', 'sklenařic', 'staré', 'vsi', 'tento', 'třiče', 've', 'staré', 'vsi', 'vysoké', 'stará', 'ves', 'poslední', 'roprachtic', \
                      'jablonci', 'roku', 'roprachticích', 'jablonce', 'jednání', 'jičína', 'končinách', 'malé', 'straně', 'vrších', 'helkovicích', \
                      'koncem', 'prahy', 'sklenařicích', 'liberci', 'nár', 'roztok', 'státního', 'tehdy', 'trhovice', 'měl', 'před', 'tyto', 'jesenném', \
                      'kopci', 'kostnici', 'národní', 'německu', 'pro', 'stanovém', 'svatodušní', 'jeseném', 'ještě', 'lidé', 'nejvíce', 'rokytnice', \
                      'ruprechticích', 'velkou', 'štědrý', 'celý', 'dle', 'jičíně', 'koupil', 'starou' ,'ves', 'třiči', 'velký', 'jiz', 'mimo', 'pohřeb', \
                      'toto', 'usnesení', 'večer', 'dcery', 'helkovic', 'jak', 'jednou', 'ježto', 'německa', 'ona', 'stále', 'brambory', 'byla', 'byli', \
                      'dnes', 'dolenci', 'dále', 'mezi', 'návštěva', 'rovněž', 'boží', 'druhý'])

@dataclass
class PatternMatch:
    words: str
    pattern_type: str
    words_in_context: str
    line_number: int

@dataclass
class ContextRule:
    pattern_type: str
    action: str  # 'whitelist' nebo 'blacklist'
    pattern: str
    before: str
    after: str
    reason: str


def load_context_rules() -> List[ContextRule]:
    """Načte pravidla pro whitelist/blacklist z CSV souboru"""
    rules = []
    rules_path = pathlib.Path(RULES_FILE)
    
    if not rules_path.exists():
        print(f"Soubor s pravidly {RULES_FILE} neexistuje, pokračuji bez pravidel")
        return rules
    
    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            # Použij pipe delimiter a trim whitespace
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:

                # Trim všechny hodnoty
                trimmed_row = {k.strip(): (v.strip() if v is not None else '') for k, v in row.items()}
                
                # Přeskoč komentáře a prázdné řádky
                if (not trimmed_row.get('TYPE') or 
                    trimmed_row.get('TYPE').startswith('#')):
                    continue
                
                rule = ContextRule(
                    pattern_type=trimmed_row.get('TYPE', '').upper(),
                    action=trimmed_row.get('ACTION', '').lower(),
                    pattern=trimmed_row.get('PATTERN', ''),
                    before=trimmed_row.get('BEFORE', ''),
                    after=trimmed_row.get('AFTER', ''),
                    reason=trimmed_row.get('REASON', '')
                )
                
                if rule.pattern_type and rule.action and rule.pattern:
                    rules.append(rule)
                    
        print(f"Načteno {len(rules)} pravidel z {RULES_FILE}")
    except Exception as e:
        print(f"Chyba při načítání pravidel: {e}")
    
    return rules


def apply_context_rules(matches: List[Tuple], text: str, rules: List[ContextRule]) -> List[Tuple]:
    """Aplikuje whitelist/blacklist pravidla na nalezené matches"""
    if not rules:
        return matches
    
    filtered_matches = []
    
    for match_data in matches:
        words, value, start, end, pattern_type = match_data[:5]
        
        # Získej kontext kolem matche
        context_start = max(0, start - 100)  # širší kontext pro pravidla
        context_end = min(len(text), end + 100)
        before_text = text[context_start:start].lower()
        after_text = text[end:context_end].lower()
        
        # Zkontroluj pravidla
        should_include = True
        applied_rule = None
        
        for rule in rules:
            if rule.pattern_type != pattern_type:
                continue
                
            # Zkontroluj jestli pattern matchuje
            if rule.pattern.lower() not in value.lower():
                continue
                
            # Zkontroluj kontext před
            if rule.before and rule.before != '*':
                if rule.before.lower() not in before_text:
                    continue
                    
            # Zkontroluj kontext po
            if rule.after and rule.after != '*':
                if rule.after.lower() not in after_text:
                    continue
            
            # Pravidlo matchuje
            applied_rule = rule
            if rule.action == 'blacklist':
                should_include = False
            elif rule.action == 'whitelist':
                should_include = True
            break  # první matchující pravidlo vyhrává
        
        if should_include:
            filtered_matches.append(match_data)
        elif applied_rule:
            print(f"Blacklisted: {pattern_type} '{value}' - {applied_rule.reason}")
    
    return filtered_matches


###########################################################

def extract_address_numbers(text: str) -> List[Tuple[str, str, int, int]]:
   """Extrahuje čísla adres ve formátu č. 999 včetně seznamů"""
   matches = []
   
   # Pattern pro č. následované seznamem čísel: "č. 10, 33, 58 a 27"
   pattern = r'\b[čćĆČcC]\.?\s*(\d+(?:\s*[,]\s*\d+)*(?:\s+a\s+\d+)?)\b'
   
   for match in re.finditer(pattern, text):
       full_match = match.group(0)
       numbers_part = match.group(1)
       start_pos = match.start()
       end_pos = match.end()
       
       # Extrahuj jednotlivá čísla ze seznamu
       # Nejdřív nahraď "a" čárkou pro sjednocení
       normalized = re.sub(r'\s+a\s+', ', ', numbers_part)
       # Pak extrahuj všechna čísla
       individual_numbers = re.findall(r'\d+', normalized)
       
       # Přidej každé číslo jako samostatný match
       for number in individual_numbers:
           if 1 <= len(number) <= 4:  # ověř délku čísla (1-4 číslice)
               matches.append((full_match, number, start_pos, end_pos))
   
   return matches


# ---------------------------------------------------------

def extract_years(text: str) -> List[Tuple[str, str, int, int]]:
    """
    Extrahuje roky v různých formátech.
    - Samostatná 3–4ciferná čísla (500–2000), s vyloučením jednotek.
    - Vylučuje části tisícových formátů s mezerami („9 876“, „12 345“).
    - Formát „14 [16/6] 68“: rok = <první dvě číslice><poslední dvě číslice> -> 1468.
      Např. „19 [20/2] 21“ -> 1921.
    Vrací list tuple: (plný_záchyt, rok_jako_string, start, end).
    """
    matches: List[Tuple[str, str, int, int]] = []

    # Jednotky/etikety, které nesmí následovat po čísle (aby to nebyl rok)
    unit_after = r'(?:kg|K\.|K\b|zl\.|Kčs?|osob|l|sáh(?:u|ů|y)?|obyvatel(?:ů|é|e)?|m|km|kop|%|str\.|stran)'

    # --- Pattern 1: samostatné roky (3–4 číslice) bez jednotek ---
    pattern1 = rf'\b(\d{{3,4}})(?!\s*(?:{unit_after})\b)'
    for m in re.finditer(pattern1, text, flags=re.IGNORECASE):
        year = int(m.group(1))
        if 500 <= year <= 2000:
            start = m.start()
            end = m.end()

            # Neber druhou/prostřední část tisícovky s mezerou: "... 9 876"
            before = text[max(0, start - 12):start]
            if re.search(r'\d+\s+$', before):
                continue

            # Neber první část "123 456": za rokem by následovala mezera a tři číslice
            after = text[end:end + 6]
            if re.match(r'^\s+\d{3}\b', after):
                continue

            matches.append((m.group(0), m.group(1), start, end))

    # --- Pattern 2: "14 [16/6] 68" -> spoj první dvě a poslední dvě číslice ---
    pattern2 = r'\b(\d{2})\s*\[\s*\d{1,2}\s*/\s*\d{1,2}\s*\]\s*(\d{2})\b'
    for m in re.finditer(pattern2, text):
        prefix2 = m.group(1)   # první dvě číslice (např. "14", "19")
        suffix2 = m.group(2)   # poslední dvě číslice (např. "68", "21")
        full_year = int(prefix2 + suffix2)  # např. "14" + "68" -> 1468

        if 500 <= full_year <= 2000:
            matches.append((m.group(0), str(full_year), m.start(), m.end()))

    return matches

# ---------------------------------------------------------

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


def extract_names(text: str) -> List[Tuple[str, str, int, int]]:
    """Extrahuje jména podle definovaných pravidel"""
    matches = []
    
    base_forms = get_base_forms('./data/name_base_form.jsonl')

    # Pattern pro jména:
    # - Začíná velkým písmenem
    # - Může obsahovat zkratku s tečkou (F., Frant.)
    # - Může obsahovat "z" pro šlechtické názvy
    # - Slova oddělená mezerami
    
    # Složitější pattern který pokrývá různé případy
    pattern = r'\b(?:[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]*\.?\s+)*[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]*(?:\s+z\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]*)?'
    
    for match in re.finditer(pattern, text):
        name_candidate = match.group(0).strip()
        
        # Filtruj podle blacklistu
        words_in_name = name_candidate.split()
        if any(word.lower().rstrip('.') in NAME_BLACKLIST for word in words_in_name):
            continue
            
        # Základní validace - alespoň jedno slovo musí být delší než 2 znaky
        if any(len(word.rstrip('.')) > 2 for word in words_in_name):
            name_value = base_forms.get(name_candidate, name_candidate)
            matches.append((name_candidate, name_value, match.start(), match.end()))
    
    return matches


# ---------------------------------------------------------

def extract_events(text: str) -> List[Tuple[str, str, int, int]]:
    """Extrahuje události podle definovaných pravidel"""
    matches = []
    base_forms = get_base_forms('./data/event_base_form.jsonl')

    # Match word characters (handles Czech diacritics)
    pattern = r'\b\w+\b'
    
    for match in re.finditer(pattern, text):
        word = match.group(0).lower()  # Consider case normalization

        if word in base_forms.keys():
            event_value = base_forms[word]
            matches.append((word, event_value, match.start(), match.end()))
    
    return matches


###########################################################

def get_context(text: str, start_pos: int, end_pos: int, context_length: int) -> str:
    """Získá kontext kolem nalezeného patternu"""
    before_start = max(0, start_pos - context_length)
    after_end = min(len(text), end_pos + context_length)
    
    context = text[before_start:after_end]
    # Označit nalezený pattern v kontextu
    pattern_in_context = text[start_pos:end_pos]
    context_before = text[before_start:start_pos]
    context_after = text[end_pos:after_end]
    
    return f"{context_before}>>>{pattern_in_context}<<<{context_after}"


def find_line_number(text: str, position: int) -> int:
    """Najde číslo řádku pro danou pozici v textu"""
    return text[:position].count('\n') + 1


def handle_pattern(words: str, pattern_type: str, words_in_context: str, line_number: int, value: str, output_file):
    """Handler pro zpracování nalezeného patternu - generuje JSONL"""
    # Odstraň všechny line breaky z řetězců
    clean_words = words.replace('\n', ' ').replace('\r', '')
    clean_context = words_in_context.replace('\n', ' ').replace('\r', '')
    clean_value = value.replace('\n', ' ').replace('\r', '')
    
    # Vytvoř JSON objekt
    entry = {
        "type": pattern_type,
        "value": clean_value,
        "line": line_number,
        "full_match": clean_words,
        "context": clean_context
    }
    
    # Zapiš jako JSONL řádek
    output_file.write(json.dumps(entry, ensure_ascii=False) + '\n')


def process_text(text: str, output_file) -> int:
    """Zpracuje text a najde všechny patterny"""
    total_matches = 0
    
    # Načti pravidla pro kontext
    rules = load_context_rules()
    
    # Najdi všechny patterny
    address_matches = extract_address_numbers(text)
    year_matches = extract_years(text)
    name_matches = extract_names(text)
    event_matches = extract_events(text)
    
    # Převeď na jednotný formát s typem
    all_matches = []
    
    for words, value, start, end in address_matches:
        all_matches.append((words, value, start, end, "ADDRESS"))
    
    for words, value, start, end in year_matches:
        all_matches.append((words, value, start, end, "YEAR"))
    
    for words, value, start, end in name_matches:
        all_matches.append((words, value, start, end, "NAME"))

    for words, value, start, end in event_matches:
        all_matches.append((words, value, start, end, "EVENT"))

    # Aplikuj context rules
    filtered_matches = apply_context_rules(all_matches, text, rules)
    
    # Připrav finální data pro řazení
    final_matches = []
    for words, value, start, end, pattern_type in filtered_matches:
        context = get_context(text, start, end, CONTEXT_LENGTH)
        line_num = find_line_number(text, start)
        final_matches.append((pattern_type, value, start, words, pattern_type, context, line_num, value))
    
    # Seřaď podle typu (první) a hodnoty (druhé)
    final_matches.sort(key=lambda x: (x[0], x[1]))
    
    # Zpracuj všechny nálezy
    for type_sort, value_sort, position, words, pattern_type, context, line_num, value in final_matches:
        handle_pattern(words, pattern_type, context, line_num, value, output_file)
        total_matches += 1


###########################################################

def main():
    # Kontrola existence vstupního souboru
    input_path = pathlib.Path(INPUT_MD_FILE)
    if not input_path.exists():
        print(f"❌ Chyba: Soubor {INPUT_MD_FILE} neexistuje!")
        return
    
    # Vytvoř ukázkový soubor s pravidly pokud neexistuje
    rules_path = pathlib.Path(RULES_FILE)
    if not rules_path.exists():
        print(f"Vytvářím ukázkový soubor s pravidly: {RULES_FILE}")
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            f.write("TYPE    | ACTION    | PATTERN | BEFORE | AFTER    | REASON\n")
            # f.write("YEAR    | blacklist | 1500    | platil | Kč       | money amount\n")
            # f.write("NAME    | whitelist | Josef   |        | Janda    | force person name\n")
            # f.write("ADDRESS | blacklist | 123     | str.   |          | page number\n")
            f.write("# Komentáře začínající # jsou ignorovány\n")
    
    print(f"Načítám {INPUT_MD_FILE}...")
    text = input_path.read_text(encoding='utf-8')
    print(f"Načteno: {len(text)} znaků")
    
    print("Hledám patterny...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as output_file:
        total_matches = process_text(text, output_file)
    
    print(f"✅ Hotovo! Nalezeno {total_matches} patternů")
    print(f"Výsledky uloženy do: {OUTPUT_FILE}")
    print(f"Pravidla pro úpravy: {RULES_FILE}")
    
    # Zobraz statistiky
    print("\nStatistiky:")
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        address_count = content.count("ADDRESS")
        year_count = content.count("YEAR") 
        name_count = content.count("NAME")
        event_count = content.count("EVENT")
        
        print(f"  Adresy: {address_count}")
        print(f"  Roky: {year_count}")
        print(f"  Jména: {name_count}")
        print(f"  Události: {event_count}")



if __name__ == "__main__":
    main()