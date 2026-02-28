#!/usr/bin/env bash
# batch_parse_remaining_ot.sh - Parse all remaining Old Testament books
# Starting from Joshua (book 6) through Malachi (book 39)
# Genesis-Deuteronomy (books 1-5) already completed

set -uo pipefail

cd /Users/joshua/work/strong_number_embedding/sn_within_unv_selfgroup_segmentation

# Verse counts for each chapter of each book (from standard Bible verse counts)
# Format: BOOK_VERSES[chapter]=verse_count

parse_book() {
    local book="$1"
    shift
    local verse_counts=("$@")
    local total_chapters=${#verse_counts[@]}

    echo ""
    echo "========================================"
    echo "Starting $book ($total_chapters chapters)"
    echo "========================================"

    local total_verses=0
    local processed=0
    local errors=0

    for ((chap=1; chap<=total_chapters; chap++)); do
        local verse_count=${verse_counts[$((chap-1))]}
        total_verses=$((total_verses + verse_count))

        # Create output directory
        mkdir -p "output/$book/$chap"

        echo -n "Chapter $chap ($verse_count verses): "

        for ((verse=1; verse<=verse_count; verse++)); do
            if python run_parser_temp.py --book "$book" "$chap" "$verse" >/dev/null 2>&1; then
                echo -n "."
                processed=$((processed + 1))
            else
                echo -n "x"
                errors=$((errors + 1))
            fi
        done
        echo " done"
    done

    echo "[$book] Processed: $processed, Errors: $errors, Total verses: $total_verses"
    echo ""
}

# Log file for this batch run
LOG_FILE="output/batch_remaining_ot_$(date +%Y%m%d_%H%M%S).log"

{
echo "Starting batch parse of remaining OT books at $(date)"
echo "=========================================="

# Joshua (24 chapters)
JOSH_VERSES=(18 24 17 24 15 27 26 35 27 44 23 24 33 25 26 7 12 13 27 33 9 31 19 14)
parse_book "Josh" "${JOSH_VERSES[@]}"

# Judges (21 chapters)
JUDG_VERSES=(36 23 31 24 31 40 25 35 57 18 40 15 25 20 20 31 13 25 27 4 2)
parse_book "Judg" "${JUDG_VERSES[@]}"

# Ruth (4 chapters)
RUTH_VERSES=(22 23 18 22)
parse_book "Ruth" "${RUTH_VERSES[@]}"

# 1 Samuel (31 chapters)
SAM1_VERSES=(28 36 21 22 12 21 17 22 27 27 15 25 23 52 35 23 58 30 24 42 15 23 29 22 44 25 12 25 11 31 13)
parse_book "1Sam" "${SAM1_VERSES[@]}"

# 2 Samuel (24 chapters)
SAM2_VERSES=(27 32 39 12 25 23 29 18 13 19 27 31 39 33 37 23 29 33 43 26 22 51 39 25)
parse_book "2Sam" "${SAM2_VERSES[@]}"

# 1 Kings (22 chapters)
KGS1_VERSES=(53 46 28 34 18 38 51 66 28 29 43 33 34 31 34 34 24 46 21 43 29 53)
parse_book "1Kgs" "${KGS1_VERSES[@]}"

# 2 Kings (25 chapters)
KGS2_VERSES=(18 25 27 44 27 33 20 29 37 36 21 21 25 29 38 20 41 37 37 21 26 20 37 20 30)
parse_book "2Kgs" "${KGS2_VERSES[@]}"

# 1 Chronicles (29 chapters)
CHR1_VERSES=(54 55 24 43 26 81 40 40 44 14 47 40 14 17 29 43 27 17 19 8 30 19 32 31 31 32 34 21 30)
parse_book "1Chr" "${CHR1_VERSES[@]}"

# 2 Chronicles (36 chapters)
CHR2_VERSES=(17 18 17 22 14 42 22 18 31 19 23 16 22 15 19 14 19 34 11 37 20 12 21 27 28 23 9 27 36 27 21 33 25 33 27 23)
parse_book "2Chr" "${CHR2_VERSES[@]}"

# Ezra (10 chapters)
EZRA_VERSES=(11 70 13 24 17 22 28 36 15 44)
parse_book "Ezra" "${EZRA_VERSES[@]}"

# Nehemiah (13 chapters)
NEH_VERSES=(11 20 32 38 22 4 23 29 30 38 36 21 21)
parse_book "Neh" "${NEH_VERSES[@]}"

# Esther (10 chapters)
ESTH_VERSES=(22 23 15 17 14 14 10 17 32 3)
parse_book "Esth" "${ESTH_VERSES[@]}"

# Job (42 chapters)
JOB_VERSES=(22 13 26 21 27 30 21 22 35 22 20 25 28 22 35 22 16 21 29 29 34 30 17 25 6 14 23 28 25 31 40 22 33 37 16 33 24 41 30 24 34 17)
parse_book "Job" "${JOB_VERSES[@]}"

# Psalms (150 chapters)
PS_VERSES=(6 12 8 8 12 10 17 9 20 18 7 8 6 7 5 11 15 50 14 9 13 31 6 10 22 12 14 9 11 12 24 11 22 22 28 12 40 22 13 17 13 11 5 26 17 11 9 14 20 23 19 9 6 7 23 13 11 11 17 12 8 12 11 10 13 20 7 35 36 5 24 20 28 23 10 12 20 72 13 19 16 8 18 12 13 17 7 18 52 17 16 15 5 23 11 13 12 9 9 5 8 28 22 35 45 48 43 13 31 7 10 10 9 8 18 19 2 29 176 7 8 9 4 8 5 6 5 6 8 8 3 18 3 3 21 26 9 8 24 13 10 7 12 15 21 10 20 14 9 6)
parse_book "Ps" "${PS_VERSES[@]}"

# Proverbs (31 chapters)
PROV_VERSES=(33 22 35 27 23 35 27 36 18 32 31 28 25 35 33 33 28 24 29 30 31 29 35 34 28 28 27 28 27 33 31)
parse_book "Prov" "${PROV_VERSES[@]}"

# Ecclesiastes (12 chapters)
ECCL_VERSES=(18 26 22 16 20 12 29 17 18 20 10 14)
parse_book "Eccl" "${ECCL_VERSES[@]}"

# Song of Solomon (8 chapters)
SONG_VERSES=(17 17 11 16 16 13 13 14)
parse_book "Song" "${SONG_VERSES[@]}"

# Isaiah (66 chapters)
ISA_VERSES=(31 22 26 6 30 13 25 22 21 34 16 6 22 32 9 14 14 7 25 6 17 25 18 23 12 21 13 29 24 33 9 20 24 17 10 22 38 22 8 31 29 25 28 28 25 13 15 22 26 11 23 15 12 17 13 12 21 14 21 22 11 12 19 12 25 24)
parse_book "Isa" "${ISA_VERSES[@]}"

# Jeremiah (52 chapters)
JER_VERSES=(19 37 25 31 31 30 34 22 26 25 23 17 27 22 21 21 27 23 15 18 14 30 40 10 38 24 22 17 32 24 40 44 26 22 19 32 21 28 18 16 18 22 13 30 5 28 7 47 39 46 64 34)
parse_book "Jer" "${JER_VERSES[@]}"

# Lamentations (5 chapters)
LAM_VERSES=(22 22 66 22 22)
parse_book "Lam" "${LAM_VERSES[@]}"

# Ezekiel (48 chapters)
EZEK_VERSES=(28 10 27 17 17 14 27 18 11 22 25 28 23 23 8 63 24 32 14 49 32 31 49 27 17 21 36 26 21 26 18 32 33 31 15 38 28 23 29 49 26 20 27 31 25 24 23 35)
parse_book "Ezek" "${EZEK_VERSES[@]}"

# Daniel (12 chapters)
DAN_VERSES=(21 49 30 37 31 28 28 27 27 21 45 13)
parse_book "Dan" "${DAN_VERSES[@]}"

# Hosea (14 chapters)
HOS_VERSES=(11 23 5 19 15 11 16 14 17 15 12 14 16 9)
parse_book "Hos" "${HOS_VERSES[@]}"

# Joel (3 chapters)
JOEL_VERSES=(20 32 21)
parse_book "Joel" "${JOEL_VERSES[@]}"

# Amos (9 chapters)
AMOS_VERSES=(15 16 15 13 27 14 17 14 15)
parse_book "Amos" "${AMOS_VERSES[@]}"

# Obadiah (1 chapter)
OBAD_VERSES=(21)
parse_book "Obad" "${OBAD_VERSES[@]}"

# Jonah (4 chapters)
JONAH_VERSES=(17 10 10 11)
parse_book "Jonah" "${JONAH_VERSES[@]}"

# Micah (7 chapters)
MIC_VERSES=(16 13 12 13 15 16 20)
parse_book "Mic" "${MIC_VERSES[@]}"

# Nahum (3 chapters)
NAH_VERSES=(15 14 19)
parse_book "Nah" "${NAH_VERSES[@]}"

# Habakkuk (3 chapters)
HAB_VERSES=(17 20 19)
parse_book "Hab" "${HAB_VERSES[@]}"

# Zephaniah (3 chapters)
ZEPH_VERSES=(18 15 20)
parse_book "Zeph" "${ZEPH_VERSES[@]}"

# Haggai (2 chapters)
HAG_VERSES=(15 23)
parse_book "Hag" "${HAG_VERSES[@]}"

# Zechariah (14 chapters)
ZECH_VERSES=(21 13 10 14 11 15 14 23 17 12 17 14 9 21)
parse_book "Zech" "${ZECH_VERSES[@]}"

# Malachi (4 chapters)
MAL_VERSES=(14 17 18 6)
parse_book "Mal" "${MAL_VERSES[@]}"

echo ""
echo "=========================================="
echo "Batch parsing of remaining OT books complete at $(date)"
echo "=========================================="

} 2>&1 | tee "$LOG_FILE"

echo "Log saved to: $LOG_FILE"
