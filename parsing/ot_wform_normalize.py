#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ot_wform_normalize — turn FHL's noisy Hebrew `wform` (lparsing) into a
normalized structure + an exportable Latin code (à la NT `V-Qal-Perf-3MS`).

Motivation: see parsing/OT_PARSING_CODE_SURVEY.md. OT wform is a Chinese prose
field carrying (1) legacy `12<code>21` internal-code fragments, (2) editorial /
qere-ketiv apparatus prose, (3) mixed delimiters, (4) curly-okina binyan names,
(5) an open POS vocabulary. NT wform is already a closed tagset; this brings OT
toward the same machine-usability.

Design: conservative. We SEPARATE noise (fragments→prefixes/particles,
apparatus→notes) from the morphology core, then parse the core with controlled
vocabularies. Anything unrecognized is preserved in `residual` so nothing is
silently dropped (bedrock rule: no silent loss).

Public API:
    normalize_wform(raw: str) -> dict
    to_code(parsed: dict) -> str
Run `python3 parsing/ot_wform_normalize.py` to validate over the whole DB.
"""
import re, unicodedata

# --- legacy internal-code fragment: 12<code>21 (the non-exportable 中文內碼) ---
FRAG = re.compile(r'12(.{1,8}?)21')
# fragment -> (prefix-type, canonical particle) for the common ones (survey top set)
FRAG_PARTICLE = {
    ';h': ('Art', 'ha'),  '>w': ('Conj', 'we'), '.l': ('Prep', 'le'),
    '.B': ('Prep', 'be'), '.K': ('Prep', 'ke'), '!im': ('Prep', 'min'),
    'hwhy': ('Proper', 'YHWH'),
}

# --- apparatus / editorial prose markers -> pulled into notes, off the core ---
APPARATUS = ['這是馬所拉學者把讀型', '這是把讀型', '這是寫型', '這是寫的形式',
             '把讀型', '讀型', '寫型', '停頓型', '馬所拉',
             '按照唸的形式', '按照', '這個字應該是', '這個字', '與下一個字分成兩個字',
             '與上一個字分成兩個字', '分成兩個字']  # NB '段落符號' handled by STRUCT

# --- controlled vocabularies (Chinese -> canonical Latin) ---
POS = {  # order matters: longer keys first
    '關係代名詞':'Rel', '指示代名詞':'DemPron', '疑問代名詞':'IntPron', '不定代名詞':'IndefPron',
    '指示形容詞':'DemAdj', '指示副詞':'DemAdv', '疑問副詞':'IntAdv', '否定的副詞':'NegAdv',
    '否定副詞':'NegAdv', '連接詞或副詞':'ConjAdv', '副詞或介系詞':'AdvPrep',
    '專有名詞':'Np', '受詞記號':'OM', '關係詞':'Rel', '指示詞':'Dem', '疑問詞':'Inter',
    '代名詞':'Pron', '形容詞':'Adj', '不變化詞':'Uninfl', '否定詞':'Neg', '感嘆詞':'Interj',
    '驚嘆詞':'Interj', '驚嘆語':'Interj', '哀歎語':'Interj', '語助詞':'Ptcl', '質詞':'Ptcl',
    '實名詞':'N', '數詞':'Num', '系詞':'Cop', '綴詞':'Affix',
    '名詞':'N', '動詞':'V', '冠詞':'Art', '連接詞':'Conj', '介系詞':'Prep',
    '副詞':'Adv', '指示':'Dem', '詞':'?',
}
STEM = {  # binyan; keys use curly okina ‘ (U+2018) as stored
    'Qal':'Qal', 'Nif‘al':'Niphal', 'Pi‘el':'Piel', 'Pu‘al':'Pual',
    'Hif‘il':'Hiphil', 'Hof‘al':'Hophal', 'Hitpa‘el':'Hithpael',
    'Po‘lel':'Polel', 'Po‘el':'Poel', 'Po‘al':'Poal', 'Pilpel':'Pilpel',
    'Polel':'Polel', 'Hitpo‘lel':'Hithpolel', 'Hitpo‘el':'Hithpoel',
    'Histaf‘el':'Hishtaphel', 'Pu‘lal':'Pulal', 'Hitpal‘pel':'Hitpalpel',
    'Pulal':'Pulal',
    # Aramaic binyanim (Daniel/Ezra Aramaic sections — real text, not noise)
    'Peal':'Peal', 'Peil':'Peil', 'Pael':'Pael', 'Haphel':'Haphel',
    'Haphʿel':'Haphel', 'Aphel':'Aphel', 'Shaphel':'Shaphel', 'Saphel':'Shaphel',
    'Hitpeel':'Hitpeel', 'Hitpaal':'Hitpaal', 'Ithpeel':'Ithpeel',
    'Ithpaal':'Ithpaal', 'Hofal':'Hophal', 'Hitpolel':'Hithpolel',
}
ASPECT = {  # tense/aspect/mood
    '不定詞附屬形':'InfC', '不定詞獨立形':'InfA', '主動分詞':'PtcpAct', '被動分詞':'PtcpPass',
    '完成式':'Perf', '未完成式':'Impf', '敘述式':'Wayyiqtol', '連續式':'Weqatal',
    '祈使式':'Impv', '鼓勵式':'Cohort', '祈願式':'Juss', '命令式':'Impv', '分詞':'Ptcp',
}
GENDER = {'陽':'m', '陰':'f', '通':'c'}
NUMBER = {'單':'s', '複':'p', '雙':'d'}
STATE = {'附屬形':'c', '獨立形':'a', '附屬型':'c', '獨立型':'a'}  # construct/absolute (形/型 variants)
PROPER_SUB = ['支派名', '民族名', '人名', '地名', '國名', '族名', '神名', '月名',
              '星名', '山名', '河名', '河流名稱', '河流名', '城名', '官職名', '尊稱']
MODIFIER = ['情感的', '冠狀', '的簡短形式', '的縮短形式', '的長形式', '短寫法', '長寫法',
            '短型式', '長型式', '短形式', '長形式', '強調的', '強調', '(或陰)', '(或陽)',
            '(或單)', '(或複)', '埃及王的尊稱']  # orthographic / nuance -> note
# tokens that are whole-verse punctuation/structure, not a morpheme
STRUCT = {'段落符號': 'Para', '停頓符號': 'Pause'}

_STEM_RE = re.compile('|'.join(re.escape(k) for k in STEM))
_ASPECT_RE = re.compile('|'.join(re.escape(k) for k in sorted(ASPECT, key=len, reverse=True)))
_STATE_RE = re.compile('|'.join(re.escape(k) for k in STATE))
_POS_RE = re.compile('|'.join(re.escape(k) for k in sorted(POS, key=len, reverse=True)))

def _parse_pgn(txt):
    """person/number/gender in any order; 性/數 fillers ignored. -> (p,n,g)."""
    t = txt.replace('性', '').replace('數', '')
    p = re.search(r'[123]', t)
    n = re.search(r'[單複雙]', t)
    g = re.search(r'[陽陰通]', t)
    p = p.group() if p else None
    n = NUMBER.get(n.group()) if n else None
    g = GENDER.get(g.group()) if g else None
    return p, n, g

def _clean_text(s: str) -> str:
    s = unicodedata.normalize('NFC', s)
    s = s.replace('　', ' ').replace(',', '，')      # halfwidth->fullwidth comma
    # normalize all apostrophe/okina variants -> ‘ (U+2018) so binyan names match;
    # FHL itself mixes ASCII ' and curly ‘ (e.g. Po'el vs Po‘el) — a real inconsistency.
    s = re.sub(r"['’ʼʻ`ʼ]", '‘', s)
    s = re.sub(r'[ \t]+', ' ', s).strip()
    return s

def normalize_wform(raw):
    """raw OT wform -> structured dict. Never drops content silently (residual)."""
    out = {'raw': raw, 'prefixes': [], 'particles': [], 'pos': None, 'subtype': None,
           'stem': None, 'aspect': None, 'state': None, 'person': None, 'gender': None,
           'number': None, 'suffix': None, 'notes': [], 'residual': '', 'flags': []}
    if raw is None or raw.strip() == '':
        out['flags'].append('empty'); return out

    s = _clean_text(raw)

    # 1) extract legacy fragments -> particles (capture, then strip). These are the
    #    SAME morphemes as the Chinese prefix words (連接詞 == 12>w21), so keep them
    #    in a separate `particles` list and attach to prefixes later (no double-count).
    frags = FRAG.findall(s)
    if frags:
        out['flags'].append('had_fragment')
        for f in frags:
            typ, part = FRAG_PARTICLE.get(f, (None, f))
            out['particles'].append({'code': f, 'type': typ, 'particle': part})
    s = FRAG.sub(' ', s)

    # 2) pull apparatus / editorial prose into notes
    for m in APPARATUS:
        if m in s:
            out['notes'].append(m); s = s.replace(m, ' ')
    if out['notes']:
        out['flags'].append('apparatus_prose')
    s = re.sub(r'[ \t]+', ' ', s).strip(' ，+')

    # 2b) whole-verse structure markers (段落符號…) are not morphemes
    for k, v in STRUCT.items():
        if k in s:
            out['pos'] = v; out['flags'].append('structure')
            s = s.replace(k, ' ')
    if out['pos'] and not s.strip():
        return out

    # 3) split morphemes joined by '+'. A trailing "…詞尾" segment is the
    #    pronominal SUFFIX (not a prefix); the segment before it is the head.
    segs = [seg.strip() for seg in s.split('+') if seg.strip()]
    if segs and '詞尾' in segs[-1]:
        suf = segs.pop()
        p, n, g = _parse_pgn(suf.replace('詞尾', ''))
        out['suffix'] = (p or '') + (n or '') + (g or '') or 'yes'
    head = segs[-1] if segs else ''
    for i, seg in enumerate(segs[:-1]):        # everything before head = prefixes
        pm = _POS_RE.search(seg)
        pref = {'type': POS.get(pm.group()) if pm else None, 'text': seg}
        if i < len(out['particles']):          # attach the captured particle in order
            pref['particle'] = out['particles'][i]['particle']
        out['prefixes'].append(pref)

    # 4) parse the head: POS，[proper-subtype] [stem] [aspect] [state] [P/N/G]
    work = head
    pm = _POS_RE.search(work)
    if pm:
        out['pos'] = POS[pm.group()]; work = work[pm.end():]
    m_colon = re.search(r'[：:]', work)         # colon introduces a name/gloss -> note
    if m_colon:
        tail = work[m_colon.end():].strip()
        if tail:
            out['notes'].append(tail)
        work = work[:m_colon.start()]
    subs = []
    for sub in PROPER_SUB:
        if sub in work:
            subs.append(sub); work = work.replace(sub, ' ')
    if subs:
        out['subtype'] = '/'.join(subs)
    for mod in MODIFIER:
        if mod in work:
            out['notes'].append(mod); work = work.replace(mod, ' ')
    sm = _STEM_RE.search(work)
    if sm:
        out['stem'] = STEM[sm.group()]; work = work[:sm.start()] + work[sm.end():]
    am = _ASPECT_RE.search(work)                # consumes 不定詞附屬形/獨立形 first
    if am:
        out['aspect'] = ASPECT[am.group()]; work = work[:am.start()] + work[am.end():]
    stm = _STATE_RE.search(work)                # bare 附屬形/獨立形 = noun state
    if stm:
        out['state'] = STATE[stm.group()]; work = work[:stm.start()] + work[stm.end():]
    p, n, g = _parse_pgn(work)
    out['person'], out['number'], out['gender'] = p, n, g
    for ch in [p] + ([k for k, v in NUMBER.items() if v == n]) + ([k for k, v in GENDER.items() if v == g]):
        if ch:
            work = work.replace(ch, '', 1)
    work = work.replace('性', '').replace('數', '')

    residual = re.sub(r'[，、：:。\s]+', '', work)
    # a bare divine-name / gloss sentence left over -> note, not residual
    if residual and ('上帝' in residual or '名字' in residual or '發音' in residual):
        out['notes'].append(residual); residual = ''
    out['residual'] = residual
    if residual:
        out['flags'].append('residual')
    if out['pos'] is None:
        out['flags'].append('no_pos')
    return out

def to_code(p):
    """canonical compact Latin code, NT-style. e.g. 'H:Conj+Art+V-Qal-Perf-3ms'"""
    if 'empty' in p['flags']:
        return ''
    pre = '+'.join(x['type'] or '?' for x in p['prefixes']) if p['prefixes'] else ''
    core = [p['pos'] or '?']
    for k in ('stem', 'aspect', 'state'):
        if p[k]: core.append(p[k])
    pgn = (p['person'] or '') + (p['number'] or '') + (p['gender'] or '')
    if pgn: core.append(pgn)
    body = '-'.join(core)
    code = 'H:' + (pre + '+' if pre else '') + body
    if p['suffix']:
        code += '+sfx' + (p['suffix'] if p['suffix'] != 'yes' else '')
    return code

# ---------------- validation over the whole DB ----------------
if __name__ == '__main__':
    import sqlite3, collections, sys
    DB = '/Users/joshua/work/strong_number_embedding/original_text_preparation/source_sqlite/bible_parsing.db'
    con = sqlite3.connect(DB)
    rows = [r[0] or '' for r in con.execute("select wform from lparsing")]
    n = len(rows)
    codes = collections.Counter(); residuals = collections.Counter()
    flag_ct = collections.Counter(); no_pos_ex = []
    fully = 0
    for w in rows:
        p = normalize_wform(w)
        for f in p['flags']: flag_ct[f] += 1
        c = to_code(p); codes[c] += 1
        if p['residual']:
            residuals[p['residual']] += 1
        if w.strip() and not p['residual'] and p['pos'] is not None:
            fully += 1
        elif p['pos'] is None and w.strip() and len(no_pos_ex) < 15:
            no_pos_ex.append(w)
    nonempty = sum(1 for w in rows if w.strip())
    print(f"rows                : {n:,}  (non-empty {nonempty:,})")
    print(f"distinct RAW wform  : {len(set(rows)):,}")
    print(f"distinct NORM codes : {len(codes):,}   <- collapse target (NT baseline=776)")
    print(f"fully parsed        : {fully:,}/{nonempty:,} = {fully/nonempty*100:.1f}% (POS set, no residual)")
    print(f"flags: " + ', '.join(f'{k}={v:,}' for k,v in flag_ct.most_common()))
    print("\ntop 15 normalized codes:")
    for c,ct in codes.most_common(15):
        print(f"   {ct:>7,}  {c}")
    print(f"\nresidual (unparsed leftovers) distinct: {len(residuals):,}; top:")
    for r,ct in residuals.most_common(12):
        print(f"   {ct:>6,}  {r!r}")
    if no_pos_ex:
        print("\nno-POS examples:")
        for w in no_pos_ex[:8]: print("   |", w)
