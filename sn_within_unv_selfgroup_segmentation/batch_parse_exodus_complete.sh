#!/usr/bin/env bash
# Batch parse all chapters of Exodus (出埃及記)
# Exodus verse counts per chapter

set -euo pipefail

echo "Starting complete Exodus parsing..."
echo "Start time: $(date)"

# Define verse counts for all 40 chapters of Exodus
declare -A VERSE_COUNTS=(
    [1]=22 [2]=25 [3]=22 [4]=31 [5]=23 [6]=30 [7]=25 [8]=32 [9]=35 [10]=29
    [11]=10 [12]=51 [13]=22 [14]=31 [15]=27 [16]=36 [17]=16 [18]=27 [19]=25 [20]=26
    [21]=36 [22]=31 [23]=33 [24]=18 [25]=40 [26]=37 [27]=21 [28]=43 [29]=46 [30]=38
    [31]=18 [32]=35 [33]=23 [34]=35 [35]=35 [36]=38 [37]=29 [38]=31 [39]=43 [40]=38
)

TOTAL_VERSES=0
for count in "${VERSE_COUNTS[@]}"; do
    TOTAL_VERSES=$((TOTAL_VERSES + count))
done

echo "Total verses in Exodus: $TOTAL_VERSES"
echo ""

PROCESSED=0
FAILED=0

# Parse each chapter
for chapter in {1..40}; do
    verse_count=${VERSE_COUNTS[$chapter]}
    echo "Processing Exodus Chapter $chapter (verses 1-$verse_count)..."

    for verse in $(seq 1 $verse_count); do
        # Use --book Exod parameter for Exodus (出埃及記)
        if python run_parser_temp.py --book Exod $chapter $verse >> batch_parse_exodus_complete.log 2>&1; then
            PROCESSED=$((PROCESSED + 1))
            echo -ne "\rProcessed: $PROCESSED/$TOTAL_VERSES verses"
        else
            echo ""
            echo "ERROR: Failed to parse Exodus $chapter:$verse"
            FAILED=$((FAILED + 1))
        fi
    done

    echo ""
    echo "Completed Exodus Chapter $chapter"
    echo ""
done

echo ""
echo "===================="
echo "Parsing Complete!"
echo "End time: $(date)"
echo "Total processed: $PROCESSED"
echo "Failed: $FAILED"
echo "===================="
