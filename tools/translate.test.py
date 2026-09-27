#!/usr/bin/env python3
"""The checks of the translator against errors the reviewers found in real
machine translations, and against the right forms of the same text. No model,
no GPU:   python3 tools/translate.test.py"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('translate', os.path.join(HERE, '..', 'generator', 'translate.py'))
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)
tr.set_prose(['the proposal asks for funding for the programme and its work'])

fails = 0


def check(what, got, want):
    global fails
    if got != want:
        fails += 1
        print('FAIL', what, '- got', got, 'want', want)


# Amounts with a multiplier keep their value, however written.
for src, out, lang, ok in [
    ('with 2030 projections of 3 million farmers', 'con proyecciones de 2030 millones de agricultores', 'es', False),
    ('with 2030 projections of 3 million farmers', 'con proyecciones para 2030 de 3 millones de agricultores', 'es', True),
    ('2030 projections of 3 million farmers', '2030 名の農民', 'ja', False),
    ('2030 projections of 3 million farmers', '2030 年の予測は、農民 300万人', 'ja', True),
    ('securing $20 million in TVL', '合計 20 億ドルの TVL', 'ja', False),
    ('securing $20 million in TVL', '合計 2,000万ドルの TVL', 'ja', True),
    ('a $1–2 billion market', '年間 1〜20億ドル', 'ja', False),
    ('a $1–2 billion market', '年間 10〜20億ドル', 'ja', True),
    ('112.5 million transactions', '112.5 万件', 'ja', False),
    ('112.5 million transactions', '1億1,250万件', 'ja', True),
    ('~1M–1.2M events per year', '年間約100万〜1.2万のイベント', 'ja', False),
    ('~1M–1.2M events per year', '年間約100万〜120万件のイベント', 'ja', True),
    ('300 Million ADA', '300 ミリオン ADA', 'ja', False),
    ('300 Million ADA', '3億 ADA', 'ja', True),
    ('180 Million Durians', '180 millones de duriones', 'es', True),
    ('the ₳7.92M total', 'el total de ₳7.92M', 'es', True),
    ('M1 at Month 6, M2 at Month 12', 'M1 en el mes 6, M2 en el mes 12', 'es', True),   # not an amount
]:
    check(f'amount {src!r} -> {out!r}', tr.intact(src, out, lang), ok)

# Dollars do not become yen; 円 in a word is no currency.
check('dollars as yen', tr.intact('($1,868,266 at $0.19/₳)', '（0.19ドル/1,868,266円）', 'ja'), False)
check('ellipse is no yen', tr.intact('Tooling for Elliptical Curves', '楕円曲線向けツール', 'ja'), True)

# Dates keep day, month and year.
for src, out, lang, ok in [
    ('from epoch 613 (February 13, 2026)', 'エポック 613（13月2026日）から', 'ja', False),
    ('from epoch 613 (February 13, 2026)', 'エポック 613（2026年2月13日）から', 'ja', True),
    ('adopted on April 24, 2025', '24 年 2025 月に採択', 'ja', False),
    ('adopted on April 24, 2025', '2025年4月24日に採択', 'ja', True),
    ('from July 2026 to March 2027', '7月 2026 から3月 2027 まで', 'ja', False),
    ('from July 2026 to March 2027', '2026年7月から2027年3月まで', 'ja', True),
    ('from May 5th to July 6th, 2025', '2025年5月5日から7月6日まで', 'ja', True),
    ('starts February 13, 2026', 'empieza el 13 de febrero de 2026', 'es', True),
    ('from July 2026 to June 2027', 'de julio de 2026 a junio de 2027', 'es', True),
]:
    check(f'date {src!r} -> {out!r}', tr.intact(src, out, lang), ok)
check('Spanish date put right after the model',
      tr.apply_after(tr.LANGS['es']['after'], 'el 13 de febrero 2026 y febrero 13, 2026'),
      'el 13 de febrero de 2026 y 13 de febrero de 2026')

# Characters only Chinese uses are refused; the known ones are put right first.
check('simplified Chinese character', tr.intact('native assets', 'ネイティブ资産', 'ja'), False)
check('Japanese character', tr.intact('native assets', 'ネイティブ資産', 'ja'), True)
check('fixes after the model, Japanese',
      tr.apply_after(tr.LANGS['ja']['after'], 'カーデナノの资産と170,000,000 ローブ、提議'),
      'Cardanoの資産と170,000,000 Lovelace、提案')

# A line that comes back unchanged was not translated; a line of names may stay.
check('untranslated title', tr.untranslated('Pogun: Capital Without Compromise', 'Pogun: Capital Without Compromise', True), True)
check('title of names', tr.untranslated('IO: Hydra', 'IO: Hydra', True), False)
check('line of names in an abstract', tr.untranslated('Cardano x Draper Dragon: Orion Fund', 'Cardano x Draper Dragon: Orion Fund'), False)
check('untranslated line in an abstract',
      tr.untranslated('This proposal funds the work for the programme', 'This proposal funds the work for the programme'), True)

# Hard line breaks inside a paragraph are joined; lists, headings and sentence ends are not.
src = ('Daedalus is the only full-node wallet — it runs an embedded\nCardano node and derives all data.\n'
       'Next sentence.\n1. **Protocol Maintenance** — Node upgrades (Leios,\n   Peras), with a release\n2. Second item\n## Heading\ntext')
check('hard line breaks', tr.join_wrapped(src),
      'Daedalus is the only full-node wallet — it runs an embedded Cardano node and derives all data.\n'
      'Next sentence.\n1. **Protocol Maintenance** — Node upgrades (Leios, Peras), with a release\n2. Second item\n## Heading\ntext')

# A paragraph that recurs word for word takes its reviewed translation.
boiler = 'This Treasury Withdrawal is submitted by Intersect on behalf of the vendor, as part of the budget process of this year.'
data = {'actions': [{'anchor_hash': 'h1', 'abstract': 'First paragraph.\n\n' + boiler}]}
mem = tr.paragraph_memory(data, {'h1': {'title': 't', 'abstract': 'Primer párrafo.\n\nTEXTO REVISADO'}})
check('reviewed paragraph reused', tr.reuse('Other text.\n\n' + boiler, 'Otro texto.\n\nTexto de la máquina', mem),
      'Otro texto.\n\nTEXTO REVISADO')

# A link or an ID the original does not have (a proposal can instruct the model).
check('added link', tr.intact('Vote yes.', 'Vota sí en https://evil.example/claim.'), False)
check('added www link', tr.intact('Vote yes.', 'Vota sí en www.evil.example.'), False)
check('added pool id', tr.intact('Delegate.', 'Delega a pool1m83drqwlugdt9jn7jkz8hx3pne53acfkd539d9cj8yr92dr4k9y.'), False)
check('link from the original', tr.intact('See https://x.org/a.', 'Ver https://x.org/a.'), True)

print('translate checks:', 'all passed' if not fails else f'{fails} FAILED')
raise SystemExit(1 if fails else 0)
