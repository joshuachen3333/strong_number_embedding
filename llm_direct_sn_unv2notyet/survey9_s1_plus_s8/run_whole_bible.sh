#!/bin/bash
# Run Survey9 on whole Bible (or as far as possible)
# Uses --resume to append all books into one JSON
# Usage: ./run_whole_bible.sh [model] [ollama-url]

MODEL="${1:-deepseek-v3.1:671b-cloud}"
OLLAMA_URL="${2:-http://localhost:11434}"
OUTFILE="run_logs/s9_lcc_whole_bible_$(echo $MODEL | tr ':/' '-')_v0.1.json"

# All 66 books in Chinese abbreviation order
OT_BOOKS="創 出 利 民 申 書 士 得 撒上 撒下 王上 王下 代上 代下 拉 尼 斯 伯 詩 箴 傳 歌 賽 耶 哀 結 但 何 珥 摩 俄 拿 彌 鴻 哈 番 該 亞 瑪"
NT_BOOKS="太 可 路 約 徒 羅 林前 林後 加 弗 腓 西 帖前 帖後 提前 提後 多 門 來 雅 彼前 彼後 約一 約二 約三 猶 啟"

echo "Survey9 Whole Bible Run"
echo "Model: $MODEL"
echo "Output: $OUTFILE"
echo "Started: $(date)"
echo ""

for BOOK in $OT_BOOKS $NT_BOOKS; do
    echo "=== Running $BOOK ==="
    if [ -f "$OUTFILE" ]; then
        python3 run_survey9.py --book "$BOOK" --chap all \
            --model "$MODEL" --ollama-url "$OLLAMA_URL" \
            --resume "$OUTFILE"
    else
        python3 run_survey9.py --book "$BOOK" --chap all \
            --model "$MODEL" --ollama-url "$OLLAMA_URL" \
            --out "$OUTFILE"
    fi
    echo ""
done

echo "Completed: $(date)"
