#!/bin/bash
# Batch parse all Genesis chapters
# Verse counts per chapter (from Bible structure)
declare -A verse_counts=(
  [1]=31 [2]=25 [3]=24 [4]=26 [5]=32 [6]=22 [7]=24 [8]=22 [9]=29 [10]=32
  [11]=32 [12]=20 [13]=18 [14]=24 [15]=21 [16]=16 [17]=27 [18]=33 [19]=38 [20]=18
  [21]=34 [22]=24 [23]=20 [24]=67 [25]=34 [26]=35 [27]=46 [28]=22 [29]=35 [30]=43
  [31]=55 [32]=32 [33]=20 [34]=31 [35]=29 [36]=43 [37]=36 [38]=30 [39]=23 [40]=23
  [41]=57 [42]=38 [43]=34 [44]=34 [45]=28 [46]=34 [47]=31 [48]=22 [49]=33 [50]=26
)

total_verses=0
parsed_verses=0
uncertain_verses=0

echo "Starting batch parse of Genesis (50 chapters)..."
echo "================================================"

for chap in {1..50}; do
  verse_count=${verse_counts[$chap]}
  echo ""
  echo "Chapter $chap ($verse_count verses)..."
  
  for verse in $(seq 1 $verse_count); do
    total_verses=$((total_verses + 1))
    printf "  Gen %d:%d ... " $chap $verse
    
    # Run parser and check if output file exists
    python run_parser_temp.py $chap $verse > /dev/null 2>&1
    
    if [ -f "output/Gen/$chap/${verse}" ] || [ -f "output/Gen/$chap/${verse}_uncertain" ]; then
      # Check if output is uncertain
      if [ -f "output/Gen/$chap/${verse}_uncertain" ]; then
        echo "✓ (uncertain)"
        uncertain_verses=$((uncertain_verses + 1))
      else
        echo "✓"
      fi
      parsed_verses=$((parsed_verses + 1))
    else
      echo "✗ FAILED"
    fi
  done
done

echo ""
echo "================================================"
echo "Batch parsing complete!"
echo "Total verses: $total_verses"
echo "Parsed successfully: $parsed_verses"
echo "Uncertain verses: $uncertain_verses"
echo "Failed: $((total_verses - parsed_verses))"
