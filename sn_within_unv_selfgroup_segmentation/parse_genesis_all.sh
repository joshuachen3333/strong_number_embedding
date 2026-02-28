#!/bin/bash
# Batch parse all 50 chapters of Genesis
# Uses simple array for verse counts

set -e

echo "Starting batch parse of Genesis (all 50 chapters)..."
echo "Start time: $(date)"

# Genesis verse counts (index 0 is unused, indices 1-50 correspond to chapters)
VERSE_COUNTS=(0 31 25 24 26 32 22 24 22 29 32 32 20 18 24 21 16 27 33 38 18 34 24 20 67 34 35 46 22 35 43 55 32 20 31 29 43 36 30 23 23 57 38 34 34 28 34 31 22 33 26)

total_verses=0
successful=0
uncertain=0

# Parse each chapter
for chapter in {1..50}; do
    verse_count=${VERSE_COUNTS[$chapter]}
    echo ""
    echo "=== Parsing Genesis Chapter $chapter (${verse_count} verses) ==="

    for verse in $(seq 1 $verse_count); do
        printf "  Gen %2d:%-2d ... " $chapter $verse

        if python run_parser_temp.py $chapter $verse > /dev/null 2>&1; then
            if [ -f "output/Gen/$chapter/${verse}" ]; then
                echo "✓"
                ((successful++))
            elif [ -f "output/Gen/$chapter/${verse}_uncertain" ]; then
                echo "⚠ uncertain"
                ((uncertain++))
            else
                echo "✗ failed"
            fi
        else
            echo "✗ error"
        fi

        ((total_verses++))
    done

    echo "  Chapter $chapter complete"
done

echo ""
echo "=== Batch Parse Complete ==="
echo "End time: $(date)"
echo "Total verses processed: $total_verses"
echo "Successful: $successful"
echo "Uncertain: $uncertain"
echo ""
echo "Output location: output/Gen/{1..50}/"
