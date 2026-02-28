#!/bin/bash
# Batch parse Genesis, Exodus, and Leviticus (resilient version - continues on errors)

echo "Starting batch parse of Genesis, Exodus, and Leviticus..."
echo "========================================"

# Genesis (創世記) - 50 chapters
echo "Parsing Genesis (創世記) - 50 chapters..."
for chap in {1..50}; do
    echo "  Chapter $chap..."
    case $chap in
        1) max=31 ;; 2) max=25 ;; 3) max=24 ;; 4) max=26 ;; 5) max=32 ;;
        6) max=22 ;; 7) max=24 ;; 8) max=22 ;; 9) max=29 ;; 10) max=32 ;;
        11) max=32 ;; 12) max=20 ;; 13) max=18 ;; 14) max=24 ;; 15) max=21 ;;
        16) max=16 ;; 17) max=27 ;; 18) max=33 ;; 19) max=38 ;; 20) max=18 ;;
        21) max=34 ;; 22) max=24 ;; 23) max=20 ;; 24) max=67 ;; 25) max=34 ;;
        26) max=35 ;; 27) max=46 ;; 28) max=22 ;; 29) max=35 ;; 30) max=43 ;;
        31) max=55 ;; 32) max=32 ;; 33) max=20 ;; 34) max=31 ;; 35) max=29 ;;
        36) max=43 ;; 37) max=36 ;; 38) max=30 ;; 39) max=23 ;; 40) max=23 ;;
        41) max=57 ;; 42) max=38 ;; 43) max=34 ;; 44) max=34 ;; 45) max=28 ;;
        46) max=34 ;; 47) max=31 ;; 48) max=22 ;; 49) max=33 ;; 50) max=26 ;;
    esac
    for verse in $(seq 1 $max); do
        python3 run_parser_temp.py --book Gen $chap $verse > /dev/null 2>&1 || echo "    Warning: Gen $chap:$verse failed"
    done
done
echo "Genesis complete!"

# Exodus (出埃及記) - 40 chapters
echo "Parsing Exodus (出埃及記) - 40 chapters..."
for chap in {1..40}; do
    echo "  Chapter $chap..."
    case $chap in
        1) max=22 ;; 2) max=25 ;; 3) max=22 ;; 4) max=31 ;; 5) max=23 ;;
        6) max=30 ;; 7) max=25 ;; 8) max=32 ;; 9) max=35 ;; 10) max=29 ;;
        11) max=10 ;; 12) max=51 ;; 13) max=22 ;; 14) max=31 ;; 15) max=27 ;;
        16) max=36 ;; 17) max=16 ;; 18) max=27 ;; 19) max=25 ;; 20) max=26 ;;
        21) max=36 ;; 22) max=31 ;; 23) max=33 ;; 24) max=18 ;; 25) max=40 ;;
        26) max=37 ;; 27) max=21 ;; 28) max=43 ;; 29) max=46 ;; 30) max=38 ;;
        31) max=18 ;; 32) max=35 ;; 33) max=23 ;; 34) max=35 ;; 35) max=35 ;;
        36) max=38 ;; 37) max=29 ;; 38) max=31 ;; 39) max=43 ;; 40) max=38 ;;
    esac
    for verse in $(seq 1 $max); do
        python3 run_parser_temp.py --book Exod $chap $verse > /dev/null 2>&1 || echo "    Warning: Exod $chap:$verse failed"
    done
done
echo "Exodus complete!"

# Leviticus (利未記) - 27 chapters
echo "Parsing Leviticus (利未記) - 27 chapters..."
for chap in {1..27}; do
    echo "  Chapter $chap..."
    case $chap in
        1) max=17 ;; 2) max=16 ;; 3) max=17 ;; 4) max=35 ;; 5) max=19 ;;
        6) max=30 ;; 7) max=38 ;; 8) max=36 ;; 9) max=24 ;; 10) max=20 ;;
        11) max=47 ;; 12) max=8 ;; 13) max=59 ;; 14) max=57 ;; 15) max=33 ;;
        16) max=34 ;; 17) max=16 ;; 18) max=30 ;; 19) max=37 ;; 20) max=27 ;;
        21) max=24 ;; 22) max=33 ;; 23) max=44 ;; 24) max=23 ;; 25) max=55 ;;
        26) max=46 ;; 27) max=34 ;;
    esac
    for verse in $(seq 1 $max); do
        python3 run_parser_temp.py --book Lev $chap $verse > /dev/null 2>&1 || echo "    Warning: Lev $chap:$verse failed"
    done
done
echo "Leviticus complete!"

echo "========================================"
echo "Batch parsing complete!"
echo ""
echo "Summary:"
echo "  Genesis: $(find output/Gen -type f | wc -l | tr -d ' ') files"
echo "  Exodus: $(find output/Exod -type f 2>/dev/null | wc -l | tr -d ' ') files"
echo "  Leviticus: $(find output/Lev -type f 2>/dev/null | wc -l | tr -d ' ') files"
echo ""
echo "Total: 117 chapters"
