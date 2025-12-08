#!/usr/bin/env bash
# fetch_text.sh (fixed)
# qb.php 用 chineses；qp.php 用 engs。兩者會互相同步。
# 預設：John 3:16（約 3:16）

set -euo pipefail

# ---- 66卷中英對照表（engs<tab>chineses）----
MAP=$'Gen\t創
Exod\t出
Lev\t利
Num\t民
Deut\t申
Josh\t書
Judg\t士
Ruth\t得
1Sam\t撒上
2Sam\t撒下
1Kgs\t王上
2Kgs\t王下
1Chr\t代上
2Chr\t代下
Ezra\t拉
Neh\t尼
Esth\t斯
Job\t伯
Ps\t詩
Prov\t箴
Eccl\t傳
Song\t歌
Isa\t賽
Jer\t耶
Lam\t哀
Ezek\t結
Dan\t但
Hos\t何
Joel\t珥
Amos\t摩
Obad\t俄
Jonah\t拿
Mic\t彌
Nah\t鴻
Hab\t哈
Zeph\t番
Hag\t該
Zech\t亞
Mal\t瑪
Matt\t太
Mark\t可
Luke\t路
John\t約
Acts\t徒
Rom\t羅
1Cor\t林前
2Cor\t林後
Gal\t加
Eph\t弗
Phil\t腓
Col\t西
1Thess\t帖前
2Thess\t帖後
1Tim\t提前
2Tim\t提後
Titus\t多
Phlm\t門
Heb\t來
Jas\t雅
1Pet\t彼前
2Pet\t彼後
1John\t約一
2John\t約二
3John\t約三
Jude\t猶
Rev\t啟'

usage() {
  cat <<'EOF'
用法: fetch_text.sh [--chineses 卷] [--engs Abbr] [--chap N] [--sec M] [--list]
  --chineses, -b   中文卷名縮寫（如 創 / 約 / 撒上 / 彼前 …）
  --engs           英文縮寫（如 Gen / John / 1Sam / 1Pet …）
  --chap,   -c     章（數字）
  --sec,    -s     節（數字）
  --list           列出中英對照
預設：約 3:16（John 3:16）
注意：qb.php 只吃 chineses；qp.php 只吃 engs。腳本會自動互轉並保持一致。
EOF
}

list_books() {
  echo "English Abbr  ->  中文縮寫"
  echo "$MAP" | awk -F'\t' '{printf "  %-8s ->  %s\n",$1,$2}'
}

lookup_engs_from_chineses() {
  local c="$1"
  echo "$MAP" | awk -F'\t' -v key="$c" '$2==key{print $1; ok=1} END{exit ok?0:1}'
}

lookup_chineses_from_engs() {
  local e="$1"
  echo "$MAP" | awk -F'\t' -v key="$e" '$1==key{print $2; ok=1} END{exit ok?0:1}'
}

# ---- 預設：John 3:16（約 3:16）----
BOOK_C=""   # 留空，後面再決定（避免預設卡住互轉）
BOOK_E=""
CHAP="3"
SEC="16"

# 記錄使用者是否有明確指定（用來決定覆寫邏輯）
USER_SET_C=0
USER_SET_E=0

# ---- 參數解析 ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --list)    list_books; exit 0 ;;
    --chineses|-b)
      BOOK_C="${2:-}"; USER_SET_C=1; shift 2 ;;
    --chineses=*)
      BOOK_C="${1#*=}"; USER_SET_C=1; shift ;;
    --engs)
      BOOK_E="${2:-}"; USER_SET_E=1; shift 2 ;;
    --engs=*)
      BOOK_E="${1#*=}"; USER_SET_E=1; shift ;;
    --chap|-c)
      CHAP="${2:-}"; shift 2 ;;
    --chap=*)
      CHAP="${1#*=}"; shift ;;
    --sec|-s)
      SEC="${2:-}"; shift 2 ;;
    --sec=*)
      SEC="${1#*=}"; shift ;;
    *)
      echo "未知參數：$1" >&2; usage; exit 1 ;;
  esac
done

# ---- 驗證數字 ----
if ! [[ "$CHAP" =~ ^[0-9]+$ && "$SEC" =~ ^[0-9]+$ ]]; then
  echo "錯誤：chap/sec 需為數字。收到 chap='$CHAP' sec='$SEC'。" >&2
  exit 1
fi

# ---- 套用預設或互轉，並保持一致 ----
if (( USER_SET_C==0 && USER_SET_E==0 )); then
  # 都沒指定 → 用預設 John/約
  BOOK_E="John"
  BOOK_C="$(lookup_chineses_from_engs "$BOOK_E")"
fi

if (( USER_SET_C==1 && USER_SET_E==0 )); then
  # 只指定中文 → 強制轉 engs
  if ! BOOK_E="$(lookup_engs_from_chineses "$BOOK_C")"; then
    echo "錯誤：無法由 chineses='$BOOK_C' 對應到英文縮寫。用 --list 查看支援表。" >&2
    exit 1
  fi
fi

if (( USER_SET_C==0 && USER_SET_E==1 )); then
  # 只指定英文 → 強制轉中文
  if ! BOOK_C="$(lookup_chineses_from_engs "$BOOK_E")"; then
    echo "錯誤：無法由 engs='$BOOK_E' 對應到中文卷名。用 --list 查看支援表。" >&2
    exit 1
  fi
fi

if (( USER_SET_C==1 && USER_SET_E==1 )); then
  # 兩邊都指定 → 檢查一致性
  EXPECT_C="$(lookup_chineses_from_engs "$BOOK_E" || true)"
  if [[ -z "${EXPECT_C:-}" || "$EXPECT_C" != "$BOOK_C" ]]; then
    echo "錯誤：--chineses '$BOOK_C' 與 --engs '$BOOK_E' 不一致。" >&2
    echo "建議：只指定其中一個，或用 --list 查對照。" >&2
    exit 1
  fi
fi

# ---- 發送兩個請求 ----
command -v curl >/dev/null || { echo "請先安裝 curl"; exit 1; }
command -v jq   >/dev/null || { echo "請先安裝 jq";   exit 1; }

echo "=== qb.php（UNV + strong=1）— ${BOOK_C} ${CHAP}:${SEC} ==="
curl -sS -G "https://bible.fhl.net/json/qb.php" \
  --data-urlencode "chineses=${BOOK_C}" \
  --data-urlencode "chap=${CHAP}" \
  --data-urlencode "sec=${SEC}" \
  --data-urlencode "version=unv" \
  --data-urlencode "strong=1" \
  | jq -r
echo

# Convert book name to qp.php compatible abbreviation
# qp.php uses different abbreviations than our internal mapping
QP_BOOK_E="${BOOK_E}"
case "${BOOK_E}" in
  Exod) QP_BOOK_E="Ex" ;;
  # Add more mappings here if other books have mismatches
esac

echo "=== qp.php（parsing）— ${BOOK_C} ${CHAP}:${SEC}（engs=${QP_BOOK_E}） ==="
curl -sS -G "https://bible.fhl.net/json/qp.php" \
  --data-urlencode "engs=${QP_BOOK_E}" \
  --data-urlencode "chap=${CHAP}" \
  --data-urlencode "sec=${SEC}" \
  | jq -r
