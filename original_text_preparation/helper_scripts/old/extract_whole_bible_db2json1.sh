#!/usr/bin/env bash
#
# extract_whole_bible_db2json1.sh
# 
# This script extracts the entire Bible from a specified table in a SQLite DB
# into a nested JSON file named bible_[TABLE].json.

set -e  # exit immediately if any command fails

usage() {
  echo "Usage: $0 -f <db_file> -d <table_name>"
  echo "  -f, --file        SQLite database file"
  echo "  -d, --data-table  Table that contains the Bible text (e.g. unv, kjv)"
  exit 1
}

DB_FILE=""
TABLE_NAME=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)
      DB_FILE="$2"
      shift 2
      ;;
    -d|--data-table)
      TABLE_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# Ensure required arguments are present
if [[ -z "$DB_FILE" || -z "$TABLE_NAME" ]]; then
  usage
fi

# Name the output file based on table
OUTPUT_FILE="bible_${TABLE_NAME}.json"

# Build our SQL logic
SQL="
-- 1) Gather all verses for each (book, chapter) using the canonical order from 'main'
WITH OrderedVerses AS (
  SELECT
    m.id    AS book_id,
    m.engs  AS engs,
    t.chap  AS chap,
    t.sec   AS sec,
    t.txt   AS txt
  FROM ${TABLE_NAME} AS t
  JOIN main AS m ON t.engs = m.engs
),

-- 2) Combine verses per chapter into an array
VerseGroups AS (
  SELECT
    book_id,
    engs,
    chap,
    '[' || GROUP_CONCAT(
      JSON_OBJECT('sec', sec, 'txt', txt)
    ) || ']' AS verses
  FROM OrderedVerses
  GROUP BY engs, chap
),

-- 3) Combine chapters per book into an array
ChapterGroups AS (
  SELECT
    book_id,
    engs,
    '[' || GROUP_CONCAT(
      JSON_OBJECT(
        'chap', chap,
        'verses', json(verses)
      )
    ) || ']' AS chapters
  FROM VerseGroups
  GROUP BY engs
),

-- 4) Build a JSON object for each book
FinalBooks AS (
  SELECT
    book_id,
    JSON_OBJECT(
      'engs', engs,
      'chapters', json(chapters)
    ) AS book_obj
  FROM ChapterGroups
),

-- 5) Make a JSON array of all books in canonical order
AllBooks AS (
  SELECT
    '[' || GROUP_CONCAT(book_obj) || ']' AS books
  FROM (
    SELECT book_id, book_obj
    FROM FinalBooks
    ORDER BY book_id
  )
)

-- 6) Wrap everything under a top-level JSON object
SELECT
  JSON_OBJECT(
    'version', '${TABLE_NAME}',
    'producer', 'extract_whole_bible_db2json1.sh',
    'text', json(books)
  )
FROM AllBooks;
"

# Run the query and produce the JSON file
sqlite3 "$DB_FILE" "$SQL" > "$OUTPUT_FILE"

echo "Created $OUTPUT_FILE"
