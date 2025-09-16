import json

# Constants
INPUT_FILE = "./data/name_base_form.jsonl"

def process_jsonl_file():
    seen_lines = set()
    all_entries = []
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
                    all_entries.append((entry, line))
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON at line {line_num}: {e}")
    
    # Sort by original_name
    all_entries.sort(key=lambda x: x[0]['original_name'])
    
    print(f"Processed: {len(all_entries)} unique entries")
    print(f"To be removed: {duplicates_count} duplicates, {identical_names_count} identical names")

    # Prompt user for confirmation before writing
    print(f"\nReady to update {INPUT_FILE} with {len(all_entries)} entries.")
    user_input = input("Do you want to proceed? (y/N): ").strip().lower()

    if user_input in ['y', 'yes']:
        # Write back to same file
        with open(INPUT_FILE, 'w', encoding='utf-8') as f:
            for entry, original_line in all_entries:
                f.write(original_line + '\n')
        print(f"File updated: {INPUT_FILE}")
    else:
        print("No changes made to file.")



if __name__ == "__main__":
    process_jsonl_file()