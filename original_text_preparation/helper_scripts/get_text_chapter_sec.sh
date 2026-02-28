curl -G "https://bible.fhl.net/json/qb.php" \
    --data-urlencode "chineses=創" \
    --data-urlencode "chap=3" \
    --data-urlencode "sec=5" \
    --data-urlencode "version=unv" \
    --data-urlencode "strong=1" \
    2>/dev/null | jq -r


