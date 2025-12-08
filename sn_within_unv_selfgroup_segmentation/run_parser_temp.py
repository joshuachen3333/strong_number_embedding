import json
import re
import subprocess
import sys
import os
import time
import sqlite3

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Parser version configuration
# TODO: Update this when upgrading to a new parser version
PARSER_VERSION = "v1_8"  # Format: v1_8, v1_9, etc. (underscore-separated for Python module names)

# Point to the parser script (dynamically constructed from version)
PARSE_VERSE_SCRIPT = os.path.join(SCRIPT_DIR, f"parse_verse_{PARSER_VERSION}.py")
FETCH_TEXT_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_text.sh")
OUTPUT_BASE_DIR = os.path.join(SCRIPT_DIR, "output")

# SQLite database paths (for local queries) - relative to parent project
DB_BASE_DIR = os.path.join(SCRIPT_DIR, "..", "original_text_preparation", "source_sqlite")
BIBLE_LITTLE_DB = os.path.join(DB_BASE_DIR, "bible_little.db")  # qb data (UNV + Strong's)
BIBLE_PARSING_DB = os.path.join(DB_BASE_DIR, "bible_parsing.db")  # qp data (morphology)

# Book code mapping: API format -> SQLite format (with spaces)
BOOK_CODE_MAP = {
    "Gen": "Gen", "Ex": "Ex", "Lev": "Lev", "Num": "Num", "Deut": "Deut",
    "Josh": "Josh", "Judg": "Judg", "Ruth": "Ruth",
    "1Sam": "1 Sam", "2Sam": "2 Sam", "1Kin": "1 Kin", "2Kin": "2 Kin",
    "1Chr": "1 Chr", "2Chr": "2 Chr", "Ezra": "Ezra", "Neh": "Neh",
    "Esth": "Esth", "Job": "Job", "Ps": "Ps", "Prov": "Prov",
    "Eccl": "Eccl", "Song": "Song", "Is": "Is", "Jer": "Jer",
    "Lam": "Lam", "Ezek": "Ezek", "Dan": "Dan", "Hos": "Hos",
    "Joel": "Joel", "Amos": "Amos", "Obad": "Obad", "Jon": "Jon",
    "Mic": "Mic", "Nah": "Nah", "Hab": "Hab", "Zeph": "Zeph",
    "Hag": "Hag", "Zech": "Zech", "Mal": "Mal",
    "Matt": "Matt", "Mark": "Mark", "Luke": "Luke", "John": "John",
    "Acts": "Acts", "Rom": "Rom",
    "1Cor": "1 Cor", "2Cor": "2 Cor", "Gal": "Gal", "Eph": "Eph",
    "Phil": "Phil", "Col": "Col",
    "1Thess": "1 Thess", "2Thess": "2 Thess",
    "1Tim": "1 Tim", "2Tim": "2 Tim", "Titus": "Titus",
    "Phlm": "Philem", "Heb": "Heb", "Jas": "James",
    "1Pet": "1 Pet", "2Pet": "2 Pet",
    "1John": "1 John", "2John": "2 John", "3John": "3 John",
    "Jude": "Jude", "Rev": "Rev"
}

def get_sqlite_book_code(book):
    """Convert API-style book code to SQLite book code."""
    return BOOK_CODE_MAP.get(book, book)

def is_nt_book(book):
    """Check if book is New Testament (for selecting correct parsing table)."""
    nt_books = ["Matt", "Mark", "Luke", "John", "Acts", "Rom",
                "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col",
                "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm",
                "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John",
                "Jude", "Rev"]
    return book in nt_books

def fetch_from_sqlite(book, chapter, verse):
    """Fetch verse data from local SQLite databases."""
    sqlite_book = get_sqlite_book_code(book)

    # Query bible_little.db for qb data (UNV + Strong's)
    try:
        conn_qb = sqlite3.connect(BIBLE_LITTLE_DB)
        cursor_qb = conn_qb.cursor()
        cursor_qb.execute(
            "SELECT txt FROM unv WHERE engs=? AND chap=? AND sec=?",
            (sqlite_book, chapter, verse)
        )
        row = cursor_qb.fetchone()
        conn_qb.close()

        if row is None:
            print(f"No qb data found for {book} {chapter}:{verse} in SQLite", file=sys.stderr)
            return None, None

        bible_text = row[0]

        # Build qb_data structure matching API format
        qb_data = {
            "status": "success",
            "record_count": 1,
            "record": [{
                "engs": book,
                "chap": chapter,
                "sec": verse,
                "bible_text": bible_text
            }]
        }
    except Exception as e:
        print(f"Error querying bible_little.db: {e}", file=sys.stderr)
        return None, None

    # Query bible_parsing.db for qp data (morphology)
    try:
        conn_qp = sqlite3.connect(BIBLE_PARSING_DB)
        cursor_qp = conn_qp.cursor()

        # Use fhlwhparsing for NT, lparsing for OT
        table = "fhlwhparsing" if is_nt_book(book) else "lparsing"

        cursor_qp.execute(
            f"SELECT wid, word, sn, pro, wform, orig, exp, remark FROM {table} WHERE engs=? AND chap=? AND sec=? ORDER BY wid",
            (sqlite_book, chapter, verse)
        )
        rows = cursor_qp.fetchall()
        conn_qp.close()

        # Build qp_data structure matching API format
        record = []
        for row in rows:
            wid, word, sn, pro, wform, orig, exp, remark = row
            record.append({
                "wid": wid,
                "word": word or "",
                "sn": sn.lstrip('0') if sn else "",  # Remove leading zeros to match API format
                "pro": pro or "",
                "wform": wform or "",
                "orig": orig or "",
                "exp": exp or "",
                "remark": remark or ""
            })

        qp_data = {
            "status": "success",
            "record_count": len(record),
            "record": record
        }
    except Exception as e:
        print(f"Error querying bible_parsing.db: {e}", file=sys.stderr)
        return None, None

    return qb_data, qp_data

def fetch_from_api(book, chapter, verse):
    """Fetch verse data from FHL API (original method)."""
    fetch_command = [FETCH_TEXT_SCRIPT,
                     "--engs", book, "--chap", str(chapter), "--sec", str(verse)]

    try:
        fetch_process = subprocess.run(fetch_command, capture_output=True, text=True, check=True)
        fetch_output = fetch_process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running fetch_text.sh for {book} {chapter}:{verse}: {e.stderr}", file=sys.stderr)
        return None, None

    qb_start = fetch_output.find('=== qb.php')
    qp_start = fetch_output.find('=== qp.php')

    if qb_start == -1 or qp_start == -1:
        print(f"Could not find qb.php or qp.php output for {book} {chapter}:{verse}.", file=sys.stderr)
        return None, None

    qb_json_str_raw = fetch_output[qb_start:qp_start].strip()
    qp_json_str_raw = fetch_output[qp_start:].strip()

    # Extract only the JSON part
    qb_json_str = qb_json_str_raw[qb_json_str_raw.find('{'):qb_json_str_raw.rfind('}')+1]
    qp_json_str = qp_json_str_raw[qp_json_str_raw.find('{'):qp_json_str_raw.rfind('}')+1]

    try:
        qb_data = json.loads(qb_json_str)
        qp_data = json.loads(qp_json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {book} {chapter}:{verse}: {e}", file=sys.stderr)
        # Attempt to fix common JSON issues
        qb_json_str_fixed = qb_json_str.replace('\n', '\\n').replace('\r', '\\r')
        qp_json_str_fixed = qp_json_str.replace('\n', '\\n').replace('\r', '\\r')
        try:
            qb_data = json.loads(qb_json_str_fixed)
            qp_data = json.loads(qp_json_str_fixed)
        except json.JSONDecodeError as e_fixed:
            print(f"Failed to fix JSON for {book} {chapter}:{verse}: {e_fixed}", file=sys.stderr)
            return None, None

    return qb_data, qp_data

def run_fetch_and_parse(book, chapter, verse, use_local=True):
    """
    Fetch verse data and parse it.

    Args:
        book: Book code (e.g., "Gen", "Matt", "1Cor")
        chapter: Chapter number
        verse: Verse number
        use_local: If True (default), use local SQLite databases.
                   If False, use FHL API (slower, may hit rate limits).

    Returns:
        tuple: (parsed_output, qb_data, qp_data) or (None, None, None) on error
    """
    verse_ref = f"{book} {chapter}:{verse}"

    # Fetch data from local SQLite or API
    if use_local:
        qb_data, qp_data = fetch_from_sqlite(book, chapter, verse)
    else:
        qb_data, qp_data = fetch_from_api(book, chapter, verse)

    if qb_data is None or qp_data is None:
        return None, None, None

    # Convert to JSON strings for the parser
    qb_json_str_final = json.dumps(qb_data)
    qp_json_str_final = json.dumps(qp_data)

    # Import parser module dynamically based on PARSER_VERSION
    sys.path.insert(0, os.path.dirname(PARSE_VERSE_SCRIPT))
    parser_module_name = f"parse_verse_{PARSER_VERSION}"

    try:
        # Dynamically import the parser module
        parser_module = __import__(parser_module_name)
        parse_verse_func = getattr(parser_module, "parse_verse_v1_6")  # Function name for text output

        result = parse_verse_func(qb_json_str_final, qp_json_str_final,
                                   output_format="text", verse_ref=verse_ref)
        return result, qb_data, qp_data
    except Exception as e:
        print(f"Error running {parser_module_name} for {verse_ref}: {e}", file=sys.stderr)
        return None, None, None

if __name__ == "__main__":
    book = "Gen"  # Default book
    current_chapter = 1
    current_verse = 16 # Default to Gen 1:16
    write_to_disk = True # Default behavior
    use_local = True  # Default to local SQLite (faster, no rate limits)

    # Parse command-line arguments
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print("Usage: python run_parser_temp.py [OPTIONS] <chapter> <verse>")
        print("")
        print("Options:")
        print("  --book BOOK   Specify book code (default: Gen)")
        print("  --no-write    Don't write output to disk, print to stdout")
        print("  --api         Use FHL API instead of local SQLite (slower)")
        print("  --local       Use local SQLite databases (default)")
        print("")
        print("Examples:")
        print("  python run_parser_temp.py 1 1                    # Parse Gen 1:1 using local DB")
        print("  python run_parser_temp.py --book Matt 5 3        # Parse Matt 5:3 using local DB")
        print("  python run_parser_temp.py --book 1Cor --api 1 1  # Parse 1Cor 1:1 using API")
        sys.exit(0)

    if "--no-write" in args:
        write_to_disk = False
        args.remove("--no-write")

    # Check for --api or --local flags
    if "--api" in args:
        use_local = False
        args.remove("--api")
    if "--local" in args:
        use_local = True
        args.remove("--local")

    # Check for --book parameter
    if "--book" in args:
        book_idx = args.index("--book")
        if book_idx + 1 < len(args):
            book = args[book_idx + 1]
            args.pop(book_idx)  # Remove --book
            args.pop(book_idx)  # Remove book value
        else:
            print("Error: --book requires a value")
            print("Usage: python run_parser_temp.py [--book BOOK] [--api|--local] [--no-write] <chapter> <verse>")
            sys.exit(1)

    if len(args) == 2: # Expecting chapter and verse
        try:
            current_chapter = int(args[0])
            current_verse = int(args[1])
        except ValueError:
            print("Usage: python run_parser_temp.py [--book BOOK] [--api|--local] [--no-write] <chapter> <verse>")
            sys.exit(1)
    elif len(args) > 0:
        print("Usage: python run_parser_temp.py [--book BOOK] [--api|--local] [--no-write] <chapter> <verse>")
        sys.exit(1)

    source = "local SQLite" if use_local else "FHL API"
    print(f"Processing {book} {current_chapter}:{current_verse} (source: {source})...")
    parsed_output, qb_data, qp_data = run_fetch_and_parse(book, current_chapter, current_verse, use_local=use_local)
    
    if parsed_output is None:
        print(f"Failed to process {book} {current_chapter}:{current_verse}. Exiting.", file=sys.stderr)
        sys.exit(1)

    if write_to_disk:
        # Save output
        output_dir = os.path.join(OUTPUT_BASE_DIR, book, str(current_chapter))
        os.makedirs(output_dir, exist_ok=True)
        
        filename = str(current_verse)
        # Uncertainty handling would need to be updated to check the JSON output for a warnings field

        file_path = os.path.join(output_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(parsed_output)
        print(f"Successfully processed and saved output for {book} {current_chapter}:{current_verse} to {file_path}")
    else:
        print("--- Parsed Output (not written to disk) ---")
        print(parsed_output)
        print("--- End of Parsed Output ---")

    print("Processing complete.")