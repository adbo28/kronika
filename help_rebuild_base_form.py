import json

# Constants
INPUT_FILE = "./data/name_base_form.jsonl"

def process_jsonl_file():
    seen_lines = set()
    unique_entries = []
    duplicates_count = 0
    identical_names_count = 0
    
    # Read and deduplicate
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            if line in seen_lines:
                print(f"Duplicate found at line {line_num}: {line}")
                duplicates_count += 1
            else:
                seen_lines.add(line)
                try:
                    entry = json.loads(line)
                    # Skip if original_name equals base_form
                    if entry['original_name'] == entry['base_form']:
                        print(f"Identical names at line {line_num}: {entry['original_name']}")
                        identical_names_count += 1
                    else:
                        unique_entries.append((entry, line))
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON at line {line_num}: {e}")
    
    # Sort by original_name
    unique_entries.sort(key=lambda x: x[0]['original_name'])
    
    # Write back to same file
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        for entry, original_line in unique_entries:
            f.write(original_line + '\n')
    
    print(f"Processed: {len(unique_entries)} unique entries")
    print(f"Removed: {duplicates_count} duplicates, {identical_names_count} identical names")
    print(f"File updated: {INPUT_FILE}")

if __name__ == "__main__":
    process_jsonl_file()