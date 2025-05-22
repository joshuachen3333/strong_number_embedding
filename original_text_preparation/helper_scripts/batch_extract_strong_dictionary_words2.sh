#!/bin/bash
#
#  batch_extract_strong_dictionary_words2.sh
#  ------------------------------------------------------------
#  一次查詢、依 Strong 編號遞增排序、匯出 JSON。
#
#  用法：
#     ./batch_extract_strong_dictionary_words2.sh <start_no> <end_no> [nt|ot]
#

set -euo pipefail
DB_FILE="bible_little.db"

# ---- 參數檢查 ------------------------------------------------
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <start_strong_number> <end_strong_number> [nt|ot]" >&2
  exit 1
fi
[[ $1 =~ ^[0-9]+$ && $2 =~ ^[0-9]+$ ]] || {
  echo "Error: Start / End must be integers." >&2; exit 1; }

START=$1
END=$2
(( END > START )) || { echo "Error: End > Start required." >&2; exit 1; }

MODE=${3:-ot}
[[ $MODE == nt || $MODE == ot ]] || { echo "Error: mode must be nt|ot." >&2; exit 1; }

[[ -f $DB_FILE ]] || { echo "Error: DB '$DB_FILE' not found." >&2; exit 1; }

# ---- SQL ----------------------------------------------------
if [[ $MODE == nt ]]; then
  SQL=$(cat <<EOF
SELECT '[' || group_concat(j, ',') || ']'
FROM (
  SELECT json_object(
           'sn',   gsnum,
           'dic_text', txt,
           'dic_type', 0,
           'orig', orig
         ) AS j
  FROM   gfhl
  WHERE  CAST(substr(gsnum,1,5) AS INTEGER) BETWEEN $START AND $END
  ORDER  BY CAST(substr(gsnum,1,5) AS INTEGER), gsnum
);
EOF
)
else
  SQL=$(cat <<EOF
SELECT '[' || group_concat(j, ',') || ']'
FROM (
  SELECT json_object(
           'sn',   hsnum,
           'dic_text', txt,
           'dic_type', 1,
           'orig', orig
         ) AS j
  FROM   hfhl
  WHERE  CAST(substr(hsnum,1,5) AS INTEGER) BETWEEN $START AND $END
  ORDER  BY CAST(substr(hsnum,1,5) AS INTEGER), hsnum
);
EOF
)
fi

# ---- 查詢 & 輸出 --------------------------------------------
echo "Querying ($MODE) Strong Numbers $START–$END ..."
RAW_JSON=$(sqlite3 "$DB_FILE" "$SQL")

if [[ -z $RAW_JSON || $RAW_JSON == "null" ]]; then
  echo "No results found in the given range."
  exit 0
fi

OUTFILE="strong_number_words_dict_${START}_${END}_${MODE}.json"
echo "$RAW_JSON" | jq . > "$OUTFILE"

echo "Done. JSON data saved to $OUTFILE"
