import json
import sys
from typing import List, Dict
import time

import anthropic

from dotenv import load_dotenv

INPUT_FILE = './data/extracted_patterns.txt'
OUTPUT_FILE = './data/name_base_form.jsonl'

BATCH_SIZE = 50
BATCH_NUM_START = 101 # set to an integer for partial processing; set to None to process all
BATCH_NUM_END = 500 # set to an integer for partial processing; set to None to process all


load_dotenv()

def read_file_in_batches(filename: str, batch_size: int = BATCH_SIZE):
    """Read file in batches of specified size, keeping only the 4th column (between 3rd and 4th '|')."""
    with open(filename, 'r', encoding='utf-8') as file:
        batch = []
        for line in file:
            parts = line.strip().split('|')
            if len(parts) >= 4 and parts[0].startswith('NAME'):
                value = parts[3].strip()  # take the 4th column
                batch.append(value)
                if len(batch) == batch_size:
                    yield batch
                    batch = []
        if batch:  # yield remaining lines if any
            yield batch


def format_batch_for_prompt(batch: List[str]) -> str:
    """Format batch of lines for the prompt, removing duplicates while preserving order."""
    unique_lines = list(dict.fromkeys(batch))  # preserves first occurrence order
    return '\n'.join(unique_lines)


def process_batch_with_claude(client, batch_text: str) -> Dict[str, str]:
    """Process a batch of names using Claude API."""
    
    prompt = f"""consider the below value. I need you to process it line by line and generate another file. it will contain the exact same number of rows. 
for each row of the original list, a row like this will be added to the output file.

original_name | name_in_base_form

examples:
A Bouzková | A Bouzková
A. Koldovský | A. Koldovský
A. Šulcová | A. Šulcová
Adama Nováka | Adam Novák
Adamem z Wartemberka | Adam z Wartemberka
Adolfova | Adolf

if you are uncertain or if the value does not look like a name, the name_in_base_form should be an exact copy of the original_name

Here is the batch to process:

{batch_text}"""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            # model="claude-sonnet-4-20250514", 
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # TODO DEBUG print(f"Received response from Claude. \n\n {response_text[:500]}...\n")

        # Parse the response to extract mappings
        mappings = {}
        for line in response_text.strip().split('\n'):
            if ' | ' in line:
                original, base_form = line.split(' | ', 1)
                mappings[original.strip()] = base_form.strip()
        
        return mappings
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        return {}

def append_to_jsonl(filename: str, mappings: Dict[str, str]):
    """Append mappings to JSONL file."""
    with open(filename, 'a', encoding='utf-8') as file:
        for original, base_form in mappings.items():
            json_record = {"original_name": original, "base_form": base_form}
            file.write(json.dumps(json_record, ensure_ascii=False) + '\n')

def main():
        
    client = anthropic.Anthropic()

    print('Starting processing...')

    batch_count = 0
    total_processed = 0
    
    try:
        for batch in read_file_in_batches(INPUT_FILE, BATCH_SIZE):
            batch_count += 1

            if BATCH_NUM_START and batch_count < BATCH_NUM_START:
                print(f"Skipping batch {batch_count} (before start batch {BATCH_NUM_START})")
                continue
            elif BATCH_NUM_END and batch_count > BATCH_NUM_END:
                print(f"Reached end batch {BATCH_NUM_END}. Stopping.")
                break

            print(f"Processing batch {batch_count} ({len(batch)} lines)...")
            
            # Format batch for processing
            batch_text = format_batch_for_prompt(batch)
            
            # Process with Claude
            mappings = process_batch_with_claude(client, batch_text)
            
            if mappings:
                # Append to JSONL file
                append_to_jsonl(OUTPUT_FILE, mappings)
                total_processed += len(mappings)
                print(f"Processed {len(mappings)} names in batch {batch_count}")
            else:
                print(f"Warning: No mappings returned for batch {batch_count}")
            
            # Add a small delay to respect rate limits
            time.sleep(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Completed processing {batch_count} batches, {total_processed} total name mappings written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()