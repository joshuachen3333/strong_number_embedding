import json
import re
import subprocess
import sys
import os
import time

# Assuming parse_verse.py is in the same directory
PARSE_VERSE_SCRIPT = "/Users/joshua/work/strong_number_embedding/sn_within_unv_selfgroup_segmentation/parse_verse.py"
FETCH_TEXT_SCRIPT = "/Users/joshua/work/strong_number_embedding/sn_within_unv_selfgroup_segmentation/fetch_text.sh"
OUTPUT_BASE_DIR = "/Users/joshua/work/strong_number_embedding/sn_within_unv_selfgroup_segmentation/output/"

def run_fetch_and_parse(book, chapter, verse):
    fetch_command = [FETCH_TEXT_SCRIPT,
                     "--engs", book, "--chap", str(chapter), "--sec", str(verse)]
    
    try:
        fetch_process = subprocess.run(fetch_command, capture_output=True, text=True, check=True)
        fetch_output = fetch_process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running fetch_text.sh for {book} {chapter}:{verse}: {e.stderr}", file=sys.stderr)
        return None, None, None # Return None for all outputs

    qb_start = fetch_output.find('=== qb.php')
    qp_start = fetch_output.find('=== qp.php')

    if qb_start == -1 or qp_start == -1:
        print(f"Could not find qb.php or qp.php output in fetch_text.sh result for {book} {chapter}:{verse}.", file=sys.stderr)
        return None, None, None

    qb_json_str_raw = fetch_output[qb_start:qp_start].strip()
    qp_json_str_raw = fetch_output[qp_start:].strip()

    # Extract only the JSON part
    qb_json_str = qb_json_str_raw[qb_json_str_raw.find('{'):qb_json_str_raw.rfind('}')+1]
    qp_json_str = qp_json_str_raw[qp_json_str_raw.find('{'):qp_json_str_raw.rfind('}')+1]

    try:
        qb_data = json.loads(qb_json_str)
        qp_data = json.loads(qp_json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from fetch_text.sh output for {book} {chapter}:{verse}: {e}", file=sys.stderr)
        # Attempt to fix common JSON issues (unescaped newlines/carriage returns)
        qb_json_str_fixed = qb_json_str.replace('\n', '\\n').replace('\r', '\\r')
        qp_json_str_fixed = qp_json_str.replace('\n', '\\n').replace('\r', '\\r')
        try:
            qb_data = json.loads(qb_json_str_fixed)
            qp_data = json.loads(qp_json_str_fixed)
            print(f"Successfully fixed JSON for {book} {chapter}:{verse}.", file=sys.stderr)
        except json.JSONDecodeError as e_fixed:
            print(f"Failed to fix JSON for {book} {chapter}:{verse}: {e_fixed}", file=sys.stderr)
            return None, None, None

    # Re-dump to string to ensure proper escaping for shell argument, and to remove any extra whitespace
    qb_json_str_final = json.dumps(qb_data)
    qp_json_str_final = json.dumps(qp_data)

    # Escape single quotes for shell command arguments
    qb_json_str_escaped = qb_json_str_final.replace("'", "'\'\''")
    qp_json_str_escaped = qp_json_str_final.replace("'", "'\'\''")

    parse_command = f"python {PARSE_VERSE_SCRIPT} '" + qb_json_str_escaped + "' '" + qp_json_str_escaped + "'"
    
    try:
        parse_process = subprocess.run(parse_command, shell=True, capture_output=True, text=True, check=True)
        return parse_process.stdout, qb_data, qp_data # Also return qb_data for next/prev verse info
    except subprocess.CalledProcessError as e:
        print(f"Error running parse_verse.py for {book} {chapter}:{verse}: {e.stderr}", file=sys.stderr)
        return None, None, None

if __name__ == "__main__":
    book = "Gen"
    current_chapter = 1
    current_verse = 16 # Start from Genesis 1:16
    end_verse_chapter_1 = 31 # End of Genesis chapter 1

    # Loop to process verses
    while True:
        print(f"Processing {book} {current_chapter}:{current_verse}...")
        parsed_output, qb_data, qp_data = run_fetch_and_parse(book, current_chapter, current_verse)
        
        if parsed_output is None:
            print(f"Failed to process {book} {current_chapter}:{current_verse}. Stopping.", file=sys.stderr)
            break

        # Save output
        output_dir = os.path.join(OUTPUT_BASE_DIR, book, str(current_chapter))
        os.makedirs(output_dir, exist_ok=True)
        
        filename = str(current_verse)
        if "--- UNCERTAINTY NOTES ---" in parsed_output:
            filename = f"{current_verse}_uncertain"
            print(f"Uncertainty detected for {book} {current_chapter}:{current_verse}. Saving as {filename}.", file=sys.stderr)

        file_path = os.path.join(output_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(parsed_output)
        print(f"Successfully processed and saved output for {book} {current_chapter}:{current_verse} to {file_path}")

        # Determine next verse
        if qb_data and 'next' in qb_data and qb_data['next']:
            next_info = qb_data['next']
            next_book = next_info['engs']
            next_chapter = next_info['chap']
            next_verse = next_info['sec']

            if next_book != book or next_chapter != current_chapter or next_verse > end_verse_chapter_1:
                print(f"Reached end of desired range for {book} {current_chapter}. Stopping.")
                break
            else:
                current_book = next_book # Update current book, though it should be the same
                current_chapter = next_chapter
                current_verse = next_verse
        else:
            print(f"No 'next' verse information found for {book} {current_chapter}:{current_verse}. Stopping.", file=sys.stderr)
            break
        
        time.sleep(1) # Be polite to the API

    print("Batch processing complete.")
