#!/usr/bin/env bash
# Batch parse all chapters of Genesis
# Genesis verse counts per chapter

set -euo pipefail

echo "Starting complete Genesis parsing..."
echo "Start time: $(date)"

# Define verse counts for all 50 chapters of Genesis
declare -A VERSE_COUNTS=(
    [1]=31 [2]=25 [3]=24 [4]=26 [5]=32 [6]=22 [7]=24 [8]=22 [9]=29 [10]=32
    [11]=32 [12]=20 [13]=18 [14]=24 [15]=21 [16]=16 [17]=27 [18]=33 [19]=38 [20]=18
    [21]=34 [22]=24 [23]=20 [24]=67 [25]=34 [26]=35 [27]=46 [28]=22 [29]=35 [30]=43
    [31]=55 [32]=32 [33]=20 [34]=31 [35]=29 [36]=43 [37]=36 [38]=30 [39]=23 [40]=23
    [41]=57 [42]=38 [43]=34 [44]=34 [45]=28 [46]=34 [47]=31 [48]=22 [49]=33 [50]=26
)

TOTAL_VERSES=0
for count in "${VERSE_COUNTS[@]}"; do
    TOTAL_VERSES=$((TOTAL_VERSES + count))
done

echo "Total verses in Genesis: $TOTAL_VERSES"
echo ""

PROCESSED=0
FAILED=0

# Parse each chapter
for chapter in {1..50}; do
    verse_count=${VERSE_COUNTS[$chapter]}
    echo "Processing Genesis Chapter $chapter (verses 1-$verse_count)..."

    for verse in $(seq 1 $verse_count); do
        if python run_parser_temp.py $chapter $verse >> batch_parse_genesis_complete.log 2>&1; then
            PROCESSED=$((PROCESSED + 1))
            echo -ne "\rProcessed: $PROCESSED/$TOTAL_VERSES verses"
        else
            echo ""
            echo "ERROR: Failed to parse Genesis $chapter:$verse"
            FAILED=$((FAILED + 1))
        fi
    done

    echo ""
    echo "Completed Genesis Chapter $chapter"
    echo ""
done

echo ""
echo "===================="
echo "Parsing Complete!"
echo "End time: $(date)"
echo "Total processed: $PROCESSED"
echo "Failed: $FAILED"
echo "===================="
