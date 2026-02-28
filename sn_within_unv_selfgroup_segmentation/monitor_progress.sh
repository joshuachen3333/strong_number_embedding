#!/usr/bin/env bash
# monitor_progress.sh - Track batch parsing progress

echo "=========================================="
echo "Pentateuch Parsing Progress Monitor"
echo "=========================================="
echo ""

echo "Expected totals:"
echo "  Genesis:   50 chapters, ~1,533 verses"
echo "  Exodus:    40 chapters, ~1,213 verses"
echo "  Leviticus: 27 chapters, ~859 verses"
echo "  TOTAL:     117 chapters, ~3,605 verses"
echo ""

echo "Current Status:"
echo "----------------------------------------"

# Count parsed verses per book
gen_count=$(find output/Gen -type f 2>/dev/null | wc -l | tr -d ' ')
exo_count=$(find output/Exod -type f 2>/dev/null | wc -l | tr -d ' ')
lev_count=$(find output/Lev -type f 2>/dev/null | wc -l | tr -d ' ')
total_count=$((gen_count + exo_count + lev_count))

echo "Genesis:   $gen_count verses parsed"
echo "Exodus:    $exo_count verses parsed"
echo "Leviticus: $lev_count verses parsed"
echo "TOTAL:     $total_count verses parsed"
echo ""

# Count uncertain verses
gen_uncertain=$(find output/Gen -name "*_uncertain" 2>/dev/null | wc -l | tr -d ' ')
exo_uncertain=$(find output/Exod -name "*_uncertain" 2>/dev/null | wc -l | tr -d ' ')
lev_uncertain=$(find output/Lev -name "*_uncertain" 2>/dev/null | wc -l | tr -d ' ')
total_uncertain=$((gen_uncertain + exo_uncertain + lev_uncertain))

echo "Uncertain verses:"
echo "  Genesis:   $gen_uncertain"
echo "  Exodus:    $exo_uncertain"
echo "  Leviticus: $lev_uncertain"
echo "  TOTAL:     $total_uncertain"
echo ""

# Check if batch script is still running
if pgrep -f "batch_parse_pentateuch_first_three.sh" > /dev/null; then
    echo "Status: PARSING IN PROGRESS"
    echo ""
    echo "Latest activity:"
    tail -10 pentateuch_first_three_parse.log | grep -E "(Processing|Completed)" | tail -5
else
    echo "Status: PARSING COMPLETE or NOT RUNNING"
fi

echo ""
echo "=========================================="
echo "To view full log:"
echo "  tail -f pentateuch_first_three_parse.log"
echo ""
echo "To check issue logs:"
echo "  tail output/uncertain_or_expandable_issues.txt"
echo "  tail output/compatible_but_notable_issues.txt"
echo "  tail output/compound_prep_plus_noun.txt"
echo "=========================================="
