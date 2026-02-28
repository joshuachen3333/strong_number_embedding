#!/usr/bin/env bash
# batch_parse_pentateuch_first_three.sh
# Parse all verses from Genesis, Exodus, and Leviticus
# Based on Batch_Parsing_SOP.md

set -euo pipefail

LOG_FILE="pentateuch_first_three_parse.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Define chapter and verse structure
# Format: "BookAbbr:ChapterCount:VersesPerChapter"
# VersesPerChapter is comma-separated for each chapter

BOOKS=(
    # Genesis - 50 chapters
    "Gen:50:31,25,24,26,32,22,24,22,29,32,32,20,18,24,21,16,27,33,38,18,34,24,20,67,34,35,46,22,35,43,55,32,20,31,29,43,36,30,23,23,57,38,34,34,28,34,31,22,33,26"

    # Exodus - 40 chapters
    "Exod:40:22,25,22,31,23,30,25,32,35,29,10,51,22,31,27,36,16,27,25,26,36,31,33,18,40,37,21,43,46,38,18,35,23,35,35,38,29,31,43,38"

    # Leviticus - 27 chapters
    "Lev:27:17,16,17,35,19,30,38,36,24,20,47,8,59,57,33,34,16,30,37,27,24,33,44,23,55,46,34"
)

parse_book() {
    local book_spec="$1"

    IFS=':' read -r book_abbr chapter_count verses_per_chapter <<< "$book_spec"

    log "=========================================="
    log "Starting to parse book: $book_abbr"
    log "Total chapters: $chapter_count"
    log "=========================================="

    # Create output directory
    mkdir -p "output/$book_abbr"

    # Convert verses_per_chapter to array
    IFS=',' read -ra VERSES <<< "$verses_per_chapter"

    local total_verses=0
    local parsed_verses=0
    local uncertain_verses=0
    local failed_verses=0

    # Parse each chapter
    for ((chap=1; chap<=chapter_count; chap++)); do
        local verse_count=${VERSES[$((chap-1))]}
        mkdir -p "output/$book_abbr/$chap"

        log "Processing $book_abbr chapter $chap (${verse_count} verses)..."

        # Parse each verse in the chapter
        for ((verse=1; verse<=verse_count; verse++)); do
            ((total_verses++)) || true

            # Check if already parsed
            if [[ -f "output/$book_abbr/$chap/$verse" ]] || [[ -f "output/$book_abbr/$chap/${verse}_uncertain" ]]; then
                log "  $book_abbr $chap:$verse - already exists, skipping"
                ((parsed_verses++)) || true
                continue
            fi

            log "  Parsing $book_abbr $chap:$verse..."

            # Run parser
            if python run_parser_temp.py "$chap" "$verse" >> "$LOG_FILE" 2>&1; then
                # Check which file was created
                if [[ -f "output/$book_abbr/$chap/${verse}_uncertain" ]]; then
                    ((uncertain_verses++)) || true
                    log "    ✓ Parsed with uncertainty: $book_abbr $chap:$verse"
                elif [[ -f "output/$book_abbr/$chap/$verse" ]]; then
                    ((parsed_verses++)) || true
                    log "    ✓ Successfully parsed: $book_abbr $chap:$verse"
                else
                    ((failed_verses++)) || true
                    log "    ✗ Failed (no output file): $book_abbr $chap:$verse"
                fi
            else
                ((failed_verses++)) || true
                log "    ✗ Failed with error: $book_abbr $chap:$verse"
            fi

            # Small delay to avoid overwhelming the API
            sleep 0.5
        done

        log "  Completed $book_abbr chapter $chap"
    done

    log "=========================================="
    log "Finished parsing book: $book_abbr"
    log "Total verses: $total_verses"
    log "Successfully parsed: $parsed_verses"
    log "Parsed with uncertainty: $uncertain_verses"
    log "Failed: $failed_verses"
    log "=========================================="
    log ""
}

# Main execution
log "=========================================="
log "Starting Pentateuch (First Three Books) Batch Parse"
log "Books: Genesis, Exodus, Leviticus"
log "=========================================="
log ""

for book_spec in "${BOOKS[@]}"; do
    parse_book "$book_spec"
done

log "=========================================="
log "BATCH PARSING COMPLETE"
log "=========================================="
log ""
log "Summary Report:"
log "- Genesis: output/Gen/"
log "- Exodus: output/Exod/"
log "- Leviticus: output/Lev/"
log ""
log "To verify results:"
log "  find output/{Gen,Exod,Lev} -type f | wc -l"
log "  find output/{Gen,Exod,Lev} -name '*_uncertain' | wc -l"
log ""
log "To view issue logs:"
log "  tail -50 output/uncertain_or_expandable_issues.txt"
log "  tail -50 output/compatible_but_notable_issues.txt"
log "  tail -50 output/compound_prep_plus_noun.txt"
