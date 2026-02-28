#!/bin/bash
# Batch parse all chapters and verses of Genesis
# Based on Batch_Parsing_SOP.md workflow

# Genesis verse counts per chapter (50 chapters)
declare -a VERSE_COUNTS=(
    31  # Chapter 1
    25  # Chapter 2
    24  # Chapter 3
    26  # Chapter 4
    32  # Chapter 5
    22  # Chapter 6
    24  # Chapter 7
    22  # Chapter 8
    29  # Chapter 9
    32  # Chapter 10
    32  # Chapter 11
    20  # Chapter 12
    18  # Chapter 13
    24  # Chapter 14
    21  # Chapter 15
    16  # Chapter 16
    27  # Chapter 17
    33  # Chapter 18
    38  # Chapter 19
    18  # Chapter 20
    34  # Chapter 21
    24  # Chapter 22
    20  # Chapter 23
    67  # Chapter 24
    34  # Chapter 25
    35  # Chapter 26
    46  # Chapter 27
    22  # Chapter 28
    35  # Chapter 29
    43  # Chapter 30
    55  # Chapter 31
    32  # Chapter 32
    20  # Chapter 33
    31  # Chapter 34
    29  # Chapter 35
    43  # Chapter 36
    36  # Chapter 37
    30  # Chapter 38
    23  # Chapter 39
    23  # Chapter 40
    57  # Chapter 41
    38  # Chapter 42
    34  # Chapter 43
    34  # Chapter 44
    28  # Chapter 45
    34  # Chapter 46
    31  # Chapter 47
    22  # Chapter 48
    33  # Chapter 49
    26  # Chapter 50
)

BOOK="Gen"
OUTPUT_BASE_DIR="output"
TOTAL_VERSES=0

echo "=========================================="
echo "Starting batch parsing of Genesis"
echo "=========================================="
echo ""

# Calculate total verses
for count in "${VERSE_COUNTS[@]}"; do
    TOTAL_VERSES=$((TOTAL_VERSES + count))
done

echo "Total chapters: 50"
echo "Total verses: ${TOTAL_VERSES}"
echo ""

# Create output directories for all chapters
echo "Creating output directories..."
for chapter in {1..50}; do
    mkdir -p "${OUTPUT_BASE_DIR}/${BOOK}/${chapter}"
done
echo "Directories created."
echo ""

# Parse all verses
CURRENT_VERSE=0
for chapter in {1..50}; do
    verse_count=${VERSE_COUNTS[$((chapter-1))]}
    echo "----------------------------------------"
    echo "Processing Chapter ${chapter} (${verse_count} verses)"
    echo "----------------------------------------"

    for verse in $(seq 1 ${verse_count}); do
        CURRENT_VERSE=$((CURRENT_VERSE + 1))
        echo -n "[${CURRENT_VERSE}/${TOTAL_VERSES}] Parsing ${BOOK} ${chapter}:${verse}... "

        # Run parser
        python3 run_parser_temp.py --book ${BOOK} ${chapter} ${verse} > /dev/null 2>&1

        if [ $? -eq 0 ]; then
            echo "✓"
        else
            echo "✗ FAILED"
        fi

        # Small delay to avoid overwhelming the API
        sleep 0.1
    done

    echo "Chapter ${chapter} complete."
    echo ""
done

echo "=========================================="
echo "Batch parsing complete!"
echo "=========================================="
echo ""

# Verification
echo "Verification:"
echo "-------------"
TOTAL_FILES=$(find ${OUTPUT_BASE_DIR}/${BOOK} -type f | wc -l | tr -d ' ')
UNCERTAIN_FILES=$(find ${OUTPUT_BASE_DIR}/${BOOK} -type f -name "*_uncertain" | wc -l | tr -d ' ')

echo "Total files created: ${TOTAL_FILES}"
echo "Expected files: ${TOTAL_VERSES}"
echo "Uncertain files: ${UNCERTAIN_FILES}"

if [ ${TOTAL_FILES} -eq ${TOTAL_VERSES} ]; then
    echo "✓ All verses processed successfully!"
else
    echo "⚠ Warning: File count mismatch"
    MISSING=$((TOTAL_VERSES - TOTAL_FILES))
    echo "Missing files: ${MISSING}"
fi

echo ""
echo "Check issue logs:"
echo "  cat output/uncertain_or_expandable_issues.txt"
echo "  cat output/compatible_but_notable_issues.txt"
echo "  cat output/compound_prep_plus_noun.txt"
