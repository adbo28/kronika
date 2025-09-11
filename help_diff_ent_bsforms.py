import json

# Constants
INDEX_FILE = "./data/index_data.jsonl"
NAME_BASE_FORMS_FILE = "./data/name_base_form.jsonl"

def load_name_base_forms():
    """Load existing name base forms"""
    base_forms = set()
    try:
        with open(NAME_BASE_FORMS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    base_forms.add(data['original_name'])
    except FileNotFoundError:
        print(f"Warning: {NAME_BASE_FORMS_FILE} not found, treating as empty")
    return base_forms

def process_names():
    # Load existing base forms
    existing_base_forms = load_name_base_forms()
    
    # Track unique missing names
    missing_names = set()
    
    # Read entities from index file
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                entity = json.loads(line)
                if entity['type'] == 'NAME':
                    name_value = entity['value']
                    if name_value not in existing_base_forms:
                        missing_names.add(name_value)
    
    # Print missing names in the required format
    for name in sorted(missing_names):
        entry = {
            "original_name": name,
            "base_form": name  # Default to same value
        }
        print(json.dumps(entry, ensure_ascii=False))

if __name__ == "__main__":
    process_names()