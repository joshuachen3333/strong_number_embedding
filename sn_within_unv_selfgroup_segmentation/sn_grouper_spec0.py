#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sn_grouper_spec0.py

基於中文邊界的 UNV+SN 分組器（Spec 0）

分組規則：任意兩個相鄰「分隔符」之間的所有 SN codes 構成一組
分隔符包括：句首、中文字符、標點符號、句尾
"""

import argparse
import json
import re
import subprocess
import sys


# 66 books mapping (English <-> Chinese)
BOOK_MAPPING = {
    "Gen": "創", "Exod": "出", "Lev": "利", "Num": "民", "Deut": "申",
    "Josh": "書", "Judg": "士", "Ruth": "得", "1Sam": "撒上", "2Sam": "撒下",
    "1Kgs": "王上", "2Kgs": "王下", "1Chr": "代上", "2Chr": "代下",
    "Ezra": "拉", "Neh": "尼", "Esth": "斯", "Job": "伯", "Ps": "詩",
    "Prov": "箴", "Eccl": "傳", "Song": "歌", "Isa": "賽", "Jer": "耶",
    "Lam": "哀", "Ezek": "結", "Dan": "但", "Hos": "何", "Joel": "珥",
    "Amos": "摩", "Obad": "俄", "Jonah": "拿", "Mic": "彌", "Nah": "鴻",
    "Hab": "哈", "Zeph": "番", "Hag": "該", "Zech": "亞", "Mal": "瑪",
    "Matt": "太", "Mark": "可", "Luke": "路", "John": "約", "Acts": "徒",
    "Rom": "羅", "1Cor": "林前", "2Cor": "林後", "Gal": "加", "Eph": "弗",
    "Phil": "腓", "Col": "西", "1Thess": "帖前", "2Thess": "帖後",
    "1Tim": "提前", "2Tim": "提後", "Titus": "多", "Phlm": "門", "Heb": "來",
    "Jas": "雅", "1Pet": "彼前", "2Pet": "彼後", "1John": "約壹",
    "2John": "約貳", "3John": "約參", "Jude": "猶", "Rev": "啟"
}


def fetch_data(chineses, engs, chap, sec):
    """使用 fetch_text.sh 獲取 qb 和 qp 數據"""
    cmd = ["./fetch_text.sh", "--chineses", chineses, "--chap", str(chap), "--sec", str(sec)]

    if engs:
        cmd.extend(["--engs", engs])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"錯誤：fetch_text.sh 執行失敗", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)


def parse_fetch_output(output):
    """解析 fetch_text.sh 的輸出，提取 qb 和 qp JSON"""
    qb_json = None
    qp_json = None

    # 找到 qb.php 的 JSON
    qb_match = re.search(r'=== qb\.php.*?===\n(.*?)(?=\n===|\Z)', output, re.DOTALL)
    if qb_match:
        try:
            qb_json = json.loads(qb_match.group(1))
        except json.JSONDecodeError:
            print("錯誤：無法解析 qb.php JSON", file=sys.stderr)
            sys.exit(1)

    # 找到 qp.php 的 JSON
    qp_match = re.search(r'=== qp\.php.*?===\n(.*?)(?=\n===|\Z)', output, re.DOTALL)
    if qp_match:
        try:
            qp_json = json.loads(qp_match.group(1))
        except json.JSONDecodeError:
            print("錯誤：無法解析 qp.php JSON", file=sys.stderr)
            sys.exit(1)

    return qb_json, qp_json


def normalize_tokens(text):
    """正規化 token：移除 WH/WTH/WAH 前綴，轉換形態碼"""
    # 1. 先將 <WTH8xxx> 和 <WH8xxx> 轉為 (**8xxx)（必須在移除前綴之前）
    text = re.sub(r'<WTH(8\d{3})>', r'(**\1)', text)
    text = re.sub(r'<WH(8\d{3})>', r'(**\1)', text)

    # 2. 移除 WH/WTH/WAH 等前綴，保留完整數字（包括前導零）
    text = re.sub(r'<W[ATH]*H(\d+)>', r'<\1>', text)

    # 3. 處理 {<WAH...>} -> {<...>}，保留完整數字
    text = re.sub(r'\{<WAH(\d+)>\}', r'{<\1>}', text)

    return text


def extract_groups(text):
    """
    基於中文邊界提取 SN 分組

    分隔符：句首、中文字符、標點符號、句尾
    """
    # 正規化 tokens
    text = normalize_tokens(text)

    # 定義中文字符和標點符號的正則
    chinese_char = r'[\u4e00-\u9fff]'
    punctuation = r'[，。、；：？！「」『』（）《》\s]'

    # 分隔符：中文字或標點
    delimiter = f'({chinese_char}|{punctuation})'

    # 分割字符串，保留分隔符
    parts = re.split(delimiter, text)

    groups = []
    current_sn_codes = []

    for part in parts:
        if not part:  # 跳過空字符串
            continue

        # 如果是分隔符（中文字或標點）
        if re.match(delimiter, part):
            # 如果有累積的 SN codes，則構成一組
            if current_sn_codes:
                group_str = ''.join(current_sn_codes)
                groups.append({
                    'raw': group_str,
                    'codes': current_sn_codes.copy()
                })
                current_sn_codes = []
        else:
            # 不是分隔符，應該是 SN codes
            current_sn_codes.append(part)

    # 處理最後剩餘的 SN codes（如果有）
    if current_sn_codes:
        group_str = ''.join(current_sn_codes)
        groups.append({
            'raw': group_str,
            'codes': current_sn_codes.copy()
        })

    return groups, text


def parse_sn_group(group_str):
    """解析單個 SN 組，提取 core、prefixes、morph"""
    result = {
        'core': None,
        'prefixes': [],
        'morph': [],
        'implicit': False
    }

    # 提取所有 tokens
    # <dddd> - core or prefix
    cores_and_prefixes = re.findall(r'<(\d+)>', group_str)
    # {<dddd>} - implicit core
    implicit_cores = re.findall(r'\{<(\d+)>\}', group_str)
    # (**8xxx) or {8xxx} - morph
    explicit_morph = re.findall(r'\(\*\*(\d+)\)', group_str)
    implicit_morph = re.findall(r'\{(\d+)\}', group_str)

    # 處理 implicit core
    if implicit_cores:
        result['core'] = implicit_cores[0]
        result['implicit'] = True

    # 處理 cores and prefixes
    for code in cores_and_prefixes:
        if code.startswith('09'):  # 900x = prefix
            result['prefixes'].append(code)
        elif code.startswith('8'):  # 8xxx = morph (但這應該在 (**) 中)
            result['morph'].append(code)
        else:  # 其他 = core
            if not result['core']:  # 如果還沒有 core
                result['core'] = code

    # 處理 morph
    result['morph'].extend(explicit_morph)
    result['morph'].extend(implicit_morph)

    return result


def format_group_output(parsed_group, qp_record, debug=False):
    """格式化單個分組的輸出"""
    core = parsed_group['core']
    prefixes = parsed_group['prefixes']
    morph = parsed_group['morph']

    # 構建 SN 代碼字符串
    sn_str = ''
    for prefix in prefixes:
        sn_str += f'<{prefix}>'
    if core:
        sn_str += f'<{core}>'
    if morph:
        sn_str += f'({",".join(morph)})'

    # 從 qp_record 查找對應的詞條
    wform = ''
    exp = ''

    if qp_record and core:
        # 統一補齊到 5 位數進行匹配
        core_padded = core.zfill(5)

        for record in qp_record:
            record_sn = record.get('sn')
            if not record_sn:  # 跳過沒有 sn 的記錄（如 wid=0 的概覽記錄）
                continue

            # 統一補齊到 5 位數
            record_sn_padded = record_sn.zfill(5)

            if debug:
                print(f"DEBUG: Comparing core='{core_padded}' with sn='{record_sn_padded}'", file=sys.stderr)
            if record_sn_padded == core_padded:
                wform = record.get('wform', '')
                exp = record.get('exp', '')
                if debug:
                    print(f"DEBUG: MATCH! wform='{wform}', exp='{exp}'", file=sys.stderr)
                break

    # 格式化輸出
    output = f'{sn_str} — '
    if wform:
        output += f'{wform}「{exp}」'
    else:
        output += f'「{exp}」' if exp else '（無詞形資料）'

    return output


def main():
    parser = argparse.ArgumentParser(
        description='基於中文邊界的 UNV+SN 分組器（Spec 0）'
    )
    parser.add_argument('--engs', help='英文書卷縮寫（如 Gen, Matt）')
    parser.add_argument('--chineses', help='中文書卷縮寫（如 創, 太）')
    parser.add_argument('--chap', type=int, required=True, help='章')
    parser.add_argument('--sec', type=int, required=True, help='節')
    parser.add_argument('--debug', action='store_true', help='顯示調試信息')

    args = parser.parse_args()

    # 確定 chineses 和 engs
    if args.chineses:
        chineses = args.chineses
        engs = args.engs if args.engs else None
    elif args.engs:
        chineses = BOOK_MAPPING.get(args.engs)
        if not chineses:
            print(f"錯誤：無法找到 {args.engs} 對應的中文縮寫", file=sys.stderr)
            sys.exit(1)
        engs = args.engs
    else:
        print("錯誤：必須提供 --engs 或 --chineses", file=sys.stderr)
        sys.exit(1)

    # 獲取數據
    output = fetch_data(chineses, engs, args.chap, args.sec)
    qb_json, qp_json = parse_fetch_output(output)

    if not qb_json or 'record' not in qb_json or len(qb_json['record']) == 0:
        print("錯誤：無法獲取 qb.php 數據", file=sys.stderr)
        sys.exit(1)

    # 提取 bible_text
    bible_text = qb_json['record'][0]['bible_text']

    # 提取分組
    groups, normalized_text = extract_groups(bible_text)

    # 輸出結果
    print("=" * 60)
    print("Parsed and Formatted Text Section:")
    print("=" * 60)

    qp_records = qp_json.get('record', []) if qp_json else []
    morph_notes = []

    for i, group in enumerate(groups):
        parsed = parse_sn_group(group['raw'])

        if args.debug:
            print(f"DEBUG Group {i}: raw='{group['raw']}', parsed={parsed}", file=sys.stderr)

        # 格式化輸出
        formatted = format_group_output(parsed, qp_records, debug=args.debug)
        print(formatted)

        # 收集形態註釋
        if parsed['morph']:
            for morph_code in parsed['morph']:
                # 從 qp_records 查找形態資訊
                for record in qp_records:
                    if record.get('sn') == parsed['core']:
                        wform = record.get('wform', '')
                        if wform and morph_code in wform:
                            morph_notes.append(f"*{len(morph_notes)+1}: {wform}")
                            break

    print()
    print("=" * 60)
    print("Raw UNV+SN Source Text Section:")
    print("=" * 60)
    print(bible_text)

    if morph_notes:
        print()
        print("=" * 60)
        print("Morphology Notes Section:")
        print("=" * 60)
        for note in morph_notes:
            print(note)


if __name__ == '__main__':
    main()
