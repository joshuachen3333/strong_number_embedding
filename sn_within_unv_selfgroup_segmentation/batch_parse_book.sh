#!/usr/bin/env bash
# batch_parse_book.sh - Parse all chapters of a biblical book
# Usage: ./batch_parse_book.sh <book> <start_chapter> <end_chapter> <verses_per_chapter...>
#
# Example for Exodus (40 chapters):
# ./batch_parse_book.sh Exod 1 40 22 25 22 31 23 30 ...

set -euo pipefail

if [ $# -lt 3 ]; then
    echo "Usage: $0 <book> <start_chapter> <end_chapter> <verse_count_ch1> <verse_count_ch2> ..."
    echo "Example: $0 Exod 1 3 22 25 22"
    echo "  This will parse Exodus chapters 1-3 with 22, 25, 22 verses respectively"
    exit 1
fi

BOOK="$1"
START_CHAP="$2"
END_CHAP="$3"
shift 3

# Remaining arguments are verse counts for each chapter
VERSE_COUNTS=("$@")

# Create output directory structure
for ((chap=START_CHAP; chap<=END_CHAP; chap++)); do
    mkdir -p "output/$BOOK/$chap"
done

echo "Starting batch parse of $BOOK chapters $START_CHAP-$END_CHAP"
echo "========================================"

TOTAL_PROCESSED=0
TOTAL_ERRORS=0

for ((chap=START_CHAP; chap<=END_CHAP; chap++)); do
    # Get verse count for this chapter (index is chap - START_CHAP)
    idx=$((chap - START_CHAP))
    if [ $idx -ge ${#VERSE_COUNTS[@]} ]; then
        echo "Error: No verse count provided for chapter $chap"
        exit 1
    fi

    VERSE_COUNT="${VERSE_COUNTS[$idx]}"

    echo ""
    echo "Chapter $chap ($VERSE_COUNT verses)..."

    for ((verse=1; verse<=VERSE_COUNT; verse++)); do
        python run_parser_temp.py --book "$BOOK" "$chap" "$verse" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -n "✓"
            ((TOTAL_PROCESSED++))
        else
            echo -n "✗"
            ((TOTAL_ERRORS++))
        fi

        # Progress indicator every 10 verses
        if [ $((verse % 10)) -eq 0 ]; then
            echo -n " [$verse/$VERSE_COUNT]"
        fi
    done

    echo " [$VERSE_COUNT/$VERSE_COUNT] - Chapter $chap complete"
done

echo ""
echo "========================================"
echo "Batch parsing complete!"
echo "Total processed: $TOTAL_PROCESSED"
echo "Total errors: $TOTAL_ERRORS"
echo "========================================"
