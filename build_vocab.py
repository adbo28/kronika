import pathlib
import re
import json
from collections import Counter

INPUT_MD_FILE = "./data/output.md"
OUTPUT_JSON_FILE = "./data/word_counts.json"


def strip_markdown_formatting(text):
    """Odstraní markdown formátování z textu"""
    # Odstraň headings (# ## ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Odstraň bold a italic (**text**, *text*)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    
    # Odstraň odkazy [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Odstraň kód `code` a ```code blocks```
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Odstraň HTML tagy
    text = re.sub(r'<[^>]+>', '', text)
    
    # Odstraň markdown tabulky (řádky s |)
    text = re.sub(r'^[|].*$', '', text, flags=re.MULTILINE)
    
    return text


def extract_words(text):
    """Extrahuje slova z textu podle definovaných pravidel"""
    # Regex pro slova: alpha znaky + spojovník + diakritika
    # \w zahrnuje písmena s diakritikou, ale také číslice
    # Použijeme vlastní pattern: písmena (včetně diakritiky) + volitelný spojovník
    word_pattern = r'\b[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]+(?:-[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]+)*\b'
    
    words = re.findall(word_pattern, text)
    
    # Filtruj slova - odstraň ta co obsahují číslice
    valid_words = []
    for word in words:
        # Zkontroluj že slovo neobsahuje číslice
        if not re.search(r'\d', word):
            # Převeď na malá písmena pro normalizaci
            valid_words.append(word.lower())
    
    return valid_words


def main():
    # Kontrola existence vstupního souboru
    input_path = pathlib.Path(INPUT_MD_FILE)
    if not input_path.exists():
        print(f"❌ Chyba: Soubor {INPUT_MD_FILE} neexistuje!")
        return
    
    print(f"Načítám {INPUT_MD_FILE}...")
    text = input_path.read_text(encoding='utf-8')
    print(f"Načteno: {len(text)} znaků")
    
    print("Odstraňuji markdown formátování...")
    clean_text = strip_markdown_formatting(text)
    
    print("Extrahuji slova...")
    words = extract_words(clean_text)
    print(f"Nalezeno: {len(words)} slov")
    
    print("Počítám frekvence...")
    word_counts = Counter(words)
    print(f"Unikátních slov: {len(word_counts)}")
    
    # Seřaď podle abecedy
    sorted_counts = dict(sorted(word_counts.items()))
    
    print(f"Ukládám do {OUTPUT_JSON_FILE}...")
    output_path = pathlib.Path(OUTPUT_JSON_FILE)
    
    # Uložení s českým kódováním a pěkným formátováním
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(sorted_counts, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Hotovo!")
    print(f"Prvních 10 slov (abecedně):")
    for word, count in list(sorted_counts.items())[:10]:
        print(f"  {word}: {count}")


if __name__ == "__main__":
    main()