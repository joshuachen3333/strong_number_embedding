#!/bin/bash

# Batch parse all Genesis verses
# Genesis chapter verse counts:
VERSE_COUNTS=(
    31 25 24 26 32 22 24 22 29 32  # Chapters 1-10
    32 20 18 24 21 16 27 33 38 18  # Chapters 11-20
    34 24 20 67 34 35 46 22 35 43  # Chapters 21-30
    55 32 20 31 29 43 36 30 23 23  # Chapters 31-40
    57 38 34 34 28 25 33 23 26 20  # Chapters 41-50
)

BOOK="Gen"
TOTAL_VERSES=0
PROCESSED=0
FAILED=0

# Calculate total verses
for count in "${VERSE_COUNTS[@]}"; do
    TOTAL_VERSES=$((TOTAL_VERSES + count))
done

echo "Starting batch parse of Genesis (50 chapters, $TOTAL_VERSES verses)"
echo "=============================================="

START_TIME=$(date +%s)

for chapter in {1..50}; do
    verse_count=${VERSE_COUNTS[$((chapter-1))]}
    echo ""
    echo "=== Processing Chapter $chapter ($verse_count verses) ==="
    
    for verse in $(seq 1 $verse_count); do
        echo -n "  Parsing $BOOK $chapter:$verse... "
        
        if python3 run_parser_temp.py --book "$BOOK" "$chapter" "$verse" > /tmp/parse_output_$$.txt 2>&1; then
            echo "OK"
            PROCESSED=$((PROCESSED + 1))
        else
            echo "FAILED"
            FAILED=$((FAILED + 1))
            cat /tmp/parse_output_$$.txt
        fi
        
        # Small delay to avoid hammering the API
        sleep 0.1
    done
    
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    echo "Chapter $chapter complete. Total processed: $PROCESSED, Failed: $FAILED, Elapsed: ${ELAPSED}s"
done

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo ""
echo "=============================================="
echo "Batch parsing complete!"
echo "Total verses: $TOTAL_VERSES"
echo "Processed: $PROCESSED"
echo "Failed: $FAILED"
echo "Total time: ${TOTAL_TIME}s"
