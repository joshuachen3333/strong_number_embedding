#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Traverse ALL OT FHL parsing codes (lparsing.wform) and characterize
(in)consistency vs the NT baseline (fhlwhparsing.wform). Offline, no API."""
import sqlite3, re, collections, unicodedata

DB = '/Users/joshua/work/strong_number_embedding/original_text_preparation/source_sqlite/bible_parsing.db'
con = sqlite3.connect(DB); cur = con.cursor()

def col(t):  # column list
    return [r[1] for r in cur.execute(f"pragma table_info({t})")]

# ---------- A. scale ----------
ot_n  = cur.execute("select count(*) from lparsing").fetchone()[0]
nt_n  = cur.execute("select count(*) from fhlwhparsing").fetchone()[0]
ot_books = [r[0] for r in cur.execute("select distinct engs from lparsing")]
print("="*70)
print("A. SCALE")
print(f"  OT lparsing morphemes : {ot_n:,}   books: {len(ot_books)}")
print(f"  NT fhlwhparsing        : {nt_n:,}")

ot = [r[0] if r[0] is not None else '' for r in cur.execute("select wform from lparsing")]
nt = [r[0] if r[0] is not None else '' for r in cur.execute("select wform from fhlwhparsing")]
ot_distinct = len(set(ot)); nt_distinct = len(set(nt))
print(f"  OT distinct wform      : {ot_distinct:,}  ({ot_distinct/ot_n*100:.1f}% of rows)")
print(f"  NT distinct wform      : {nt_distinct:,}  ({nt_distinct/nt_n*100:.1f}% of rows)")

# ---------- B. charset contrast (NT is terse ASCII; OT is Chinese prose) ----------
def charclass(s):
    has_cjk = any('一'<=c<='鿿' for c in s)
    has_ascii_alpha = any(c.isascii() and c.isalpha() for c in s)
    return has_cjk, has_ascii_alpha
ot_cjk = sum(1 for s in ot if charclass(s)[0])
nt_cjk = sum(1 for s in nt if charclass(s)[0])
print("\nB. CHARSET  (is the code Chinese-bearing?)")
print(f"  OT wform containing CJK: {ot_cjk:,}/{ot_n:,} = {ot_cjk/ot_n*100:.1f}%")
print(f"  NT wform containing CJK: {nt_cjk:,}/{nt_n:,} = {nt_cjk/nt_n*100:.1f}%")
print(f"  NT sample codes: {sorted(set(nt))[:12]}")
def avglen(x): return sum(len(s) for s in x)/max(1,len(x))
print(f"  avg wform length  OT={avglen(ot):.1f} chars   NT={avglen(nt):.1f} chars")

# ---------- C. legacy embedded internal-code fragments  12...21 ----------
FRAG = re.compile(r'12(.{1,6}?)21')
frag_rows = 0
frag_vocab = collections.Counter()
for s in ot:
    fs = FRAG.findall(s)
    if fs:
        frag_rows += 1
        for f in fs: frag_vocab['12'+f+'21'] += 1
print("\nC. LEGACY INTERNAL-CODE FRAGMENTS  (pattern 12<code>21 embedded in the Chinese)")
print(f"  OT rows carrying >=1 fragment: {frag_rows:,}/{ot_n:,} = {frag_rows/ot_n*100:.1f}%")
print(f"  distinct fragment tokens     : {len(frag_vocab)}")
for tok,c in frag_vocab.most_common(25):
    print(f"    {tok:12s} x{c:>7,}")

# ---------- D. delimiter / structure inconsistency ----------
print("\nD. DELIMITER / STRUCTURE INCONSISTENCY")
fw_comma = sum(1 for s in ot if '，' in s)
hw_comma = sum(1 for s in ot if ',' in s)
plus     = sum(1 for s in ot if '+' in s)
lead_sp  = sum(1 for s in ot if s[:1]==' ')
trail_sp = sum(1 for s in ot if s[-1:]==' ')
dbl_sp   = sum(1 for s in ot if '  ' in s)
empty    = sum(1 for s in ot if s.strip()=='')
print(f"  fullwidth '，' rows : {fw_comma:,}")
print(f"  halfwidth ','  rows : {hw_comma:,}   <- mixed delimiter if both present")
print(f"  '+' morpheme-join   : {plus:,}")
print(f"  leading-space rows  : {lead_sp:,}")
print(f"  trailing-space rows : {trail_sp:,}")
print(f"  double-space rows   : {dbl_sp:,}")
print(f"  EMPTY wform rows    : {empty:,}")

# ---------- E. POS / morphology vocabulary (after stripping fragments) ----------
def strip_frag(s): return FRAG.sub('', s)
pos_lead = collections.Counter()
term_vocab = collections.Counter()
POS_TERMS = ['動詞','名詞','冠詞','連接詞','介系詞','形容詞','代名詞','副詞','疑問詞',
             '感嘆詞','指示詞','關係詞','數詞','質詞','否定詞','不變化詞','專有名詞','綴詞']
STEM = ['Qal','Nifal','Niphal','Piel','Pual','Hifil','Hiphil','Hofal','Hophal',
        'Hitpael','Hithpael','Polel','Pilpel','Poal','Hishtafel']
for s in ot:
    b = strip_frag(s).strip()
    # leading POS = first CJK token before space/comma/+
    m = re.match(r'[一-鿿]+', b)
    if m: pos_lead[m.group()] += 1
    for t in re.split(r'[\s，,+]+', b):
        if t: term_vocab[t]+=1
print("\nE. LEADING-POS DISTRIBUTION (first Chinese token of each OT wform)")
for t,c in pos_lead.most_common(20):
    print(f"    {t:8s} x{c:>7,}")
print(f"  distinct leading-POS tokens: {len(pos_lead)}")

# stems present?
print("\n  Hebrew binyan/stem term spellings actually found:")
found_stem = collections.Counter()
allwform = '\n'.join(ot)
for st in STEM:
    c = allwform.count(st)
    if c: found_stem[st]=c
for st,c in found_stem.most_common():
    print(f"    {st:10s} x{c:>7,}")

# ---------- F. anomaly rows ----------
print("\nF. ANOMALY ROWS")
# placeholder-like (sn 00000 or word '+')
ph = cur.execute("select count(*) from lparsing where sn='00000' or word='+' ").fetchone()[0]
no_pos = sum(1 for s in ot if s.strip() and not re.match(r'\s*[一-鿿]', strip_frag(s)))
print(f"  placeholder rows (sn=00000 or word='+') : {ph:,}")
print(f"  wform not leading with a Chinese POS     : {no_pos:,}")
# distinct wform NOT matching a known POS lead
unknown_lead = [t for t in pos_lead if t not in POS_TERMS]
print(f"  leading tokens NOT in known POS set ({len(unknown_lead)}): {unknown_lead[:30]}")

# ---------- G. concrete inconsistency examples ----------
print("\nG. SAME-LEMMA, VARIANT-CODE EXAMPLES (does one Hebrew lemma get inconsistent wform?)")
# pick a few high-freq SN and show distinct wform variants
rows = cur.execute("""select sn, count(distinct wform) v, count(*) n from lparsing
                      where sn!='' group by sn order by v desc limit 6""").fetchall()
for sn,v,n in rows:
    variants = [r[0] for r in cur.execute(
        "select distinct wform from lparsing where sn=? limit 4",(sn,))]
    print(f"  SN {sn}: {v} distinct wform over {n} occ; e.g.:")
    for w in variants: print(f"      | {w}")
print("\nDONE")
