#!/bin/bash

# Batch parse Pentateuch (Torah) - 5 Books of Moses
# Book data: (English abbreviation, verse counts per chapter)

parse_book() {
    local BOOK=$1
    shift
    local VERSE_COUNTS=("$@")
    local CHAPTER_COUNT=${#VERSE_COUNTS[@]}
    
    local TOTAL_VERSES=0
    for count in "${VERSE_COUNTS[@]}"; do
        TOTAL_VERSES=$((TOTAL_VERSES + count))
    done
    
    local PROCESSED=0
    local FAILED=0
    local START_TIME=$(date +%s)
    
    echo ""
    echo "=========================================="
    echo "Starting batch parse of $BOOK ($CHAPTER_COUNT chapters, $TOTAL_VERSES verses)"
    echo "=========================================="
    
    # Create directories
    for chapter in $(seq 1 $CHAPTER_COUNT); do
        mkdir -p output/$BOOK/$chapter
    done
    
    for chapter in $(seq 1 $CHAPTER_COUNT); do
        verse_count=${VERSE_COUNTS[$((chapter-1))]}
        echo ""
        echo "=== $BOOK Chapter $chapter ($verse_count verses) ==="
        
        for verse in $(seq 1 $verse_count); do
            echo -n "  $BOOK $chapter:$verse... "
            
            if python3 run_parser_temp.py --book "$BOOK" "$chapter" "$verse" > /tmp/parse_output_$$.txt 2>&1; then
                echo "OK"
                PROCESSED=$((PROCESSED + 1))
            else
                echo "FAILED"
                FAILED=$((FAILED + 1))
            fi
            
            sleep 0.1
        done
        
        local CURRENT_TIME=$(date +%s)
        local ELAPSED=$((CURRENT_TIME - START_TIME))
        echo "  Chapter $chapter done. Processed: $PROCESSED, Failed: $FAILED, Elapsed: ${ELAPSED}s"
    done
    
    local END_TIME=$(date +%s)
    local TOTAL_TIME=$((END_TIME - START_TIME))
    
    echo ""
    echo "$BOOK complete! Verses: $TOTAL_VERSES, Processed: $PROCESSED, Failed: $FAILED, Time: ${TOTAL_TIME}s"
    echo "=========================================="
}

# Exodus (出埃及記) - 40 chapters
EXOD_VERSES=(
    22 25 22 31 23 30 25 32 35 29  # 1-10
    10 51 22 31 27 36 16 27 25 26  # 11-20
    36 31 33 18 40 37 21 43 46 38  # 21-30
    18 35 23 35 35 38 29 31 43 38  # 31-40
)

# Leviticus (利未記) - 27 chapters  
LEV_VERSES=(
    17 16 17 35 19 30 38 36 24 20  # 1-10
    47 8 59 57 33 34 16 30 37 27   # 11-20
    24 33 44 23 55 46 34            # 21-27
)

# Numbers (民數記) - 36 chapters
NUM_VERSES=(
    54 34 51 49 31 27 89 26 23 36  # 1-10
    35 16 33 45 41 50 13 32 22 29  # 11-20
    35 41 30 25 18 65 23 31 40 16  # 21-30
    54 42 56 29 34 13              # 31-36
)

# Deuteronomy (申命記) - 34 chapters
DEUT_VERSES=(
    46 37 29 49 33 25 26 20 29 22  # 1-10
    32 32 18 29 23 22 20 22 21 20  # 11-20
    23 30 25 22 19 19 26 68 29 20  # 21-30
    30 52 29 12                     # 31-34
)

# Parse based on argument
case "$1" in
    "Exod"|"exodus"|"2")
        parse_book "Exod" "${EXOD_VERSES[@]}"
        ;;
    "Lev"|"leviticus"|"3")
        parse_book "Lev" "${LEV_VERSES[@]}"
        ;;
    "Num"|"numbers"|"4")
        parse_book "Num" "${NUM_VERSES[@]}"
        ;;
    "Deut"|"deuteronomy"|"5")
        parse_book "Deut" "${DEUT_VERSES[@]}"
        ;;
    "all")
        parse_book "Exod" "${EXOD_VERSES[@]}"
        parse_book "Lev" "${LEV_VERSES[@]}"
        parse_book "Num" "${NUM_VERSES[@]}"
        parse_book "Deut" "${DEUT_VERSES[@]}"
        ;;
    *)
        echo "Usage: $0 {Exod|Lev|Num|Deut|all}"
        echo "  Exod (2) - Exodus 出埃及記 (40 chapters, 1213 verses)"
        echo "  Lev  (3) - Leviticus 利未記 (27 chapters, 859 verses)"
        echo "  Num  (4) - Numbers 民數記 (36 chapters, 1288 verses)"
        echo "  Deut (5) - Deuteronomy 申命記 (34 chapters, 959 verses)"
        echo "  all     - Parse all 4 books in sequence"
        exit 1
        ;;
esac
