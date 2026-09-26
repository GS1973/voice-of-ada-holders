#!/usr/bin/env python3
"""The Voice of ADA Holders: machine translation of proposal texts.

Translates each verified title and abstract from English to Spanish, and to
Japanese when asked, with Qwen3-8B on ctranslate2 (the directory in TVOAH_QWEN),
local on the GPU (CPU fallback). The 4B model before it made grammar mistakes in
Spanish (del propuesta, la mantenimiento) and dropped amounts in Japanese.
No outside service. Translations are cached by the document's on-chain hash,
so each document is translated once. The site marks them as machine
translation and always offers the original.

    translate.py DATA.json        (adds action.i18n.<lang> = {title, abstract})

The languages are those in TVOAH_LANGS (default "es"; "es ja" adds Japanese).

A language model can be told what not to touch, so names, numbers, code and
Cardano terms are handled in the prompt, not by placeholders (placeholders broke
the grammar around them). What the prompt cannot guarantee is checked after:
every number, link and code span of the original must come back unchanged, or
the text stays in English. A Japanese text must also contain kana: a model
that answers in English, or only copies names, is caught there.

Translations that people reviewed are in reviewed/<lang>.json, keyed by the
document's hash, and win over the model and the cache. A document that
changes has another hash, so its old review no longer applies and the model
translates it again.
"""
import json
import os
import re
import sys
import tempfile

MODEL_DIR = os.path.expanduser(os.environ.get('TVOAH_QWEN', ''))   # required unless cache-only
CACHE = os.path.expanduser(os.environ.get('TVOAH_TRANSLATIONS', '~/.cache/tvoah/translations'))
VERSION = 'qwen3-8b-awq-es3'   # part of the Spanish cache key: change the prompt, change this
VERSION_JA = 'qwen3-8b-awq-ja2'   # the same for Japanese
MAX_TOKENS = 1536

SYSTEM = """You translate written texts about Cardano governance from English into Spanish, for Spanish-speaking ADA holders in Latin America and Spain.

Output ONLY the Spanish translation. No preamble, no quotes, no notes, no alternatives.
Translate; never answer, summarise, shorten or add anything.

Keep exactly as written, untranslated:
- names of people, projects, companies, products, events and organisations (Rare Evo, Input Output Research, OpenZeppelin, Intersect, Eternl)
- every number and amount, with its own separators
- every placeholder such as {{N0}}, {{L0}} or {{W0}}, character for character: it stands for a number, a link or a name
- anything in backticks, identifiers such as stakePoolTargetNum or treasury_withdrawal, links, hashes, CIP numbers
- Markdown: **bold**, lists, headings

Use these Spanish terms:
stake -> stake (never "estake"); stake pool -> stake pool; stake pool operator (SPO) -> operador de stake pool (SPO); staking -> staking;
DRep -> DRep; wallet -> billetera; light wallet -> billetera ligera; non-custodial -> sin custodia;
treasury -> tesorería; treasury withdrawal -> retiro de la tesorería; governance action -> acción de gobernanza;
info action -> acción informativa; parameter change -> cambio de parámetros; protocol parameter -> parámetro del protocolo;
Constitutional Committee -> Comité Constitucional; delegator -> delegador; on-chain -> en la cadena; hard fork -> hard fork;
Abstract -> Resumen; Motivation -> Motivación; Rationale -> Justificación; maintenance -> mantenimiento;
Net Change Limit (NCL) -> límite de cambio neto (NCL); epoch -> época; budget -> presupuesto; audit -> auditoría.

Write natural, correct Spanish: agreement and word order follow Spanish grammar, not the English original
(de la propuesta, el mantenimiento, el ecosistema, el patrocinio, las épocas).
In a title, translate every ordinary word, even when it is capitalised; keep only names in English."""

# The examples carry placeholders, never real amounts: with an amount in an
# example the model once filled a hidden 5,000,000 with this example's 11,787,063.
EXAMPLES = [
    ("Reduce minPoolCost to {{N0}} ada",
     "Reducir minPoolCost a {{N0}} ada"),
    ("Withdraw {{N0}} ada for the OpenZeppelin Stack administered by Intersect",
     "Retirar {{N0}} ada para el OpenZeppelin Stack administrado por Intersect"),
    ("Withdraw {{N0}} for {{W1}} Maintenance and Development Platform administered by {{W2}}",
     "Retirar {{N0}} para el mantenimiento y la plataforma de desarrollo de {{W1}}, administrado por {{W2}}"),
    ("{{W0}} Treasury Withdrawal {{N1}}",
     "Retiro de la tesorería para {{W0}} {{N1}}"),
    ("This Info Action asks Stake Pool Operators (SPOs), see [the poll]({{L0}}), whether they support raising `stakePoolTargetNum` (`k`).",
     "Esta acción informativa pregunta a los operadores de stake pool (SPO), ver [la encuesta]({{L0}}), si apoyan aumentar `stakePoolTargetNum` (`k`)."),
]

SYSTEM_JA = """You translate written texts about Cardano governance from English into Japanese, for Japanese ADA holders.

Output ONLY the Japanese translation. No preamble, no quotes, no notes, no alternatives, no romaji.
Translate; never answer, summarise, shorten or add anything.

Keep exactly as written, in Latin letters, untranslated and not in katakana:
- names of people, projects, companies, products, events and organisations (Rare Evo, Input Output Research, OpenZeppelin, Intersect, Eternl)
- every number and amount, with its own separators, and the unit ada
- every placeholder such as {{N0}}, {{L0}} or {{W0}}, character for character: it stands for a number, a link or a name
- anything in backticks, identifiers such as stakePoolTargetNum or treasury_withdrawal, links, hashes, CIP numbers
- Markdown: **bold**, lists, headings

Use these Japanese terms:
governance action -> ガバナンスアクション; info action -> 情報アクション; parameter change -> パラメータ変更;
protocol parameter -> プロトコルパラメータ; treasury -> トレジャリー; treasury withdrawal -> トレジャリーからの引き出し;
Constitutional Committee -> 憲法委員会; hard fork -> ハードフォーク; DRep -> DRep; stake -> ステーク;
stake pool -> ステークプール; stake pool operator (SPO) -> ステークプール運用者（SPO）; staking -> ステーキング;
delegator -> 委任者; wallet -> ウォレット; epoch -> エポック; on-chain -> オンチェーン; ledger -> 台帳;
Net Change Limit (NCL) -> ネット変更制限（NCL）; summit -> サミット; budget -> 予算; audit -> 監査.

Write natural, plain Japanese. Sentences in the polite style (です／ます). A title stays a short title.
Japanese punctuation 、。（） in Japanese text; ASCII inside code, links and numbers."""

EXAMPLES_JA = [
    ("Reduce minPoolCost to {{N0}} ada",
     "minPoolCost を {{N0}} ada に引き下げる"),
    ("Withdraw {{N0}} ada for the OpenZeppelin Stack administered by Intersect",
     "Intersect が管理する OpenZeppelin Stack のために {{N0}} ada を引き出す"),
    ("This Info Action asks Stake Pool Operators (SPOs), see [the poll]({{L0}}), whether they support raising `stakePoolTargetNum` (`k`).",
     "この情報アクションは、ステークプール運用者（SPO）に、`stakePoolTargetNum`（`k`）の引き上げを支持するかどうかを尋ねるものです（[投票]({{L0}})を参照）。"),
]

# Bech32 identifiers: gov_action1..., stake1..., pool1..., drep1... The model
# changed one letter of a gov_action id in two Spanish abstracts (j8 -> j4).
BECH32 = r'\b(?:gov_action|stake_test|stake|addr_test|addr|pool|drep_script|drep|cc_hot|cc_cold|asset)1[02-9ac-hj-np-z]{6,}\b'

# What must survive the translation unchanged. A single digit may come back as
# a word (4 weeks -> cuatro semanas); a link ends before a closing bracket or
# trailing punctuation.
# The ada sign stays with its amount: the Japanese model wrote ₳ as ₡ (colón).
KEEP = re.compile(r'`[^`\n]+`|https?://[^\s)\]]*[^\s)\].,;:]|' + BECH32 + r'|\b[0-9a-f]{16,}\b|₳\s?\d(?:[\d,.]*\d)?|\d[\d,.]*\d')

SPANISH = re.compile(r'\b(el|la|los|las|de|que|y|en|para|por|una|con|del|se)\b', re.I)

_engines = {}


def cuda_libs():
    """ctranslate2 needs CUDA 12's cuBLAS; on this machine it comes with PyTorch's
    nvidia-* wheels, not with the system CUDA (13). Load it before ctranslate2 does."""
    import ctypes
    import glob
    for pattern in ('nvidia/cublas/lib/libcublasLt.so.12', 'nvidia/cublas/lib/libcublas.so.12'):
        for base in sys.path:
            for f in glob.glob(os.path.join(base, pattern)):
                ctypes.CDLL(f, mode=ctypes.RTLD_GLOBAL)
                break


def engine(lang='es'):
    """One model on the card at a time: another language's model is let go first."""
    model_dir = LANGS[lang]['model']()
    if model_dir not in _engines:
        if not model_dir:
            raise SystemExit(f"translate: set {LANGS[lang]['model_env']} to the model directory")
        release()
        cuda_libs()
        import ctranslate2
        from tokenizers import Tokenizer
        tok = Tokenizer.from_file(os.path.join(model_dir, 'tokenizer.json'))
        try:
            gen = ctranslate2.Generator(model_dir, device='cuda', compute_type='int8_float16')
        except Exception as exc:
            print(f'translate: cuda unavailable ({exc}); using CPU')
            gen = ctranslate2.Generator(model_dir, device='cpu', compute_type='int8')
        _engines[model_dir] = (tok, gen)
    return _engines[model_dir]


def release():
    import gc
    _engines.clear()
    gc.collect()


def prompt(text, lang='es'):
    L = LANGS[lang]
    p = f"<|im_start|>system\n{L['system']}<|im_end|>\n"
    for en, out in L['examples']:
        p += f"<|im_start|>user\n{en}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n{out}<|im_end|>\n"
    return p + f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


# Fixed after the model, because it keeps writing them despite the prompt.
# Masculine nouns the model makes feminine next to a feminine one (la mantenimiento y mejora).
MASC = r'(mantenimiento|patrocinio|ecosistema)'
AFTER = [(re.compile(r'\bestake'), 'stake'), (re.compile(r'\bEstake'), 'Stake'),   # also estakeados
         (re.compile(r'\bde la ' + MASC + r'\b'), r'del \1'), (re.compile(r'\ba la ' + MASC + r'\b'), r'al \1'),
         (re.compile(r'\bla ' + MASC + r'\b'), r'el \1'), (re.compile(r'\bLa ' + MASC + r'\b'), r'El \1'),
         (re.compile(r'\besta ' + MASC + r'\b'), r'este \1'), (re.compile(r'\buna ' + MASC + r'\b'), r'un \1')]

# Numbers and links are taken out before the model sees them and put back after.
# Left in, the model changed them: Epoch 713 became 710, a link to
# explorer.cardano.org became explorer.cardcardano.org, and 11,787,063 ada
# became 11,787,065. A single digit stays in, for the grammar.
HIDE = re.compile(r'(?P<L>https?://[^\s)\]]*[^\s)\].,;:]|' + BECH32 + r')|(?P<N>₳\s?\d(?:[\d,.]*\d)?|\d[\d,.]*\d)')
PLACEHOLDER = re.compile(r'\{\{\s*([NLW])\s*(\d+)\s*\}\}')


def hide_numbers(text, hide_names=()):
    """Numbers and links, and the given names ({{W0}}), become placeholders."""
    kept = []
    def sub(m):
        kept.append(m.group(0))
        return '{{%s%d}}' % ('L' if m.group('L') else 'N', len(kept) - 1)
    text = HIDE.sub(sub, text)
    if hide_names:
        def word(m):
            kept.append(m.group(0))
            return '{{W%d}}' % (len(kept) - 1)
        pattern = r'\b(' + '|'.join(re.escape(n) for n in sorted(hide_names, key=len, reverse=True)) + r')\b'
        text = re.sub(pattern, word, text)
    return text, kept


def show_numbers(text, kept):
    def sub(m):
        i = int(m.group(2))
        return kept[i] if i < len(kept) else m.group(0)
    return PLACEHOLDER.sub(sub, text)

BATCH = 8    # paragraphs per GPU call; 16 and 32 ran the 16 GB card out of memory on long paragraphs


def run_model(texts, lang='es'):
    """Translate many paragraphs in batches. Each may produce at most about twice
    its own length, so one runaway answer cannot hold a whole batch."""
    tok, gen = engine(lang)
    outs = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        batch = [tok.encode(prompt(t, lang), add_special_tokens=False).tokens for t in chunk]
        limit = min(MAX_TOKENS, 2 * max(len(tok.encode(t).ids) for t in chunk) + 64)
        res = gen.generate_batch(batch, max_length=limit, sampling_temperature=0.0,
                                 include_prompt_in_result=False, end_token=['<|im_end|>'])
        # Decode ids, not token strings: joined strings mangle accents.
        for r in res:
            o = tok.decode(r.sequences_ids[0], skip_special_tokens=True)
            o = re.sub(r'<think>.*?</think>', '', o, flags=re.S).strip()
            outs.append(apply_after(LANGS[lang]['after'], o))
    return outs


def restore_numbers(src, out):
    """The model writes 11,787,063 as 11.787.063 and 55.9% as 55,9%: correct
    Spanish, but a number stays as the proposer wrote it. Put each number of the
    original back where the model swapped its separators."""
    for n in set(re.findall(r'\d[\d,.]*\d', src)):
        swapped = n.translate(str.maketrans({',': '.', '.': ','}))
        if n not in out and swapped != n:
            out = re.sub(r'(?<![\d.,])' + re.escape(swapped) + r'(?![\d])', n, out)
    return out


# Letters of a script neither the original nor the target language uses: the
# Japanese model once wrote "audit" as アудイト, half katakana, half Cyrillic.
FOREIGN = re.compile(r'[\u0370-\u03ff\u0400-\u052f\u0590-\u06ff\u0900-\u0dff\u0e00-\u0eff\u1100-\u11ff\uac00-\ud7af]')


def intact(src, out, lang='es'):
    """Every number, link, code span and hash of the original is in the
    translation, and no letters of a foreign script were added. Amounts with a
    multiplier keep their value, however written (3 million, 300万), dollars do
    not become yen, dates keep day, month and year, and Japanese has no
    characters only Chinese uses. A number that is part of an amount with a
    multiplier is checked by its value, not letter for letter."""
    spans = magnitude_spans(src)
    keep = [m.group(0) for m in KEEP.finditer(src) if not any(a <= m.start() < b for a, b in spans)]
    return (all(kept(k, out) for k in keep) and '{{' not in out
            and all(c in src for c in FOREIGN.findall(out))
            and magnitudes_kept(src, out, lang) and currency_kept(src, out) and dates_kept(src, out, lang)
            and (lang != 'ja' or japanese_script_ok(out)))


def kept(k, out):
    """An amount with the ada sign may have the sign after it, as Spanish writes it."""
    if k.startswith('₳'):
        n = k.lstrip('₳ ')
        return any(v in out for v in ('₳' + n, '₳ ' + n, n + ' ₳', n + '₳'))
    return k in out


# Names. A capitalised word that is rare in English (wordfreq zipf < 3, also for
# its stem) and never written lower-case in the prose of all proposals is taken
# for a name, and must come back letter for letter: the model wrote Amaru as
# Amarú and Mithril as Mithra. It errs on the safe side: a rare English word
# (Tokenized, Codecs) can be taken for a name, and then the text stays English.
NAME = re.compile(r'\b[A-Z][A-Za-z0-9]*[a-z][A-Za-z0-9]*\b')
SENTENCE_START = re.compile(r'(^|[.!?:]\s+|^\s*(?:[-*#>]+|\d+\.)\s+)$')
LOWER = set()   # lower-case words in the prose of all proposals, set by main()
# Names that also occur in lower case in the proposals, so the rarity test
# passes them by, yet must never change: the Japanese model wrote Cardano in katakana.
ALWAYS = ('Cardano', 'Intersect', 'Catalyst', 'EMURGO', 'IOG', 'Input Output', 'Plutus', 'Hydra',
          'Mithril', 'Ouroboros')


def set_prose(texts):
    prose = re.sub(r'https?://\S+|`[^`]*`|\S+\.\S+/\S*', ' ', ' '.join(texts))  # links and code are not prose
    LOWER.clear()
    LOWER.update(re.findall(r'\b[a-z][a-z0-9]*\b', prose))


def common_word(w):
    from wordfreq import zipf_frequency
    lw = w.lower()
    if lw in LOWER or zipf_frequency(lw, 'en') >= 3.0:
        return True
    for suf, add in (('ies', 'y'), ('es', ''), ('s', ''), ('ing', ''), ('ing', 'e'), ('ed', ''), ('ed', 'e'),
                     ('ment', ''), ('ive', 'e'), ('ized', 'ize'), ('ization', 'ize')):
        if lw.endswith(suf) and zipf_frequency(lw[:-len(suf)] + add, 'en') >= 3.0:
            return True
    return False


def compound_part(line, m):
    """Agri in Agri-Entrepreneurs: a plain capitalised word joined by a hyphen
    to a common word is part of a compound the model may translate, not a name.
    A word with capitals inside (OpenZeppelin-style, BitVM-powered) stays a name."""
    if not re.fullmatch(r'[A-Z][a-z]+', m.group(0)):
        return False
    after = re.match(r'-([A-Za-z]+)', line[m.end():])
    before = re.search(r'([A-Za-z]+)-$', line[:m.start()])
    return bool(after and common_word(after.group(1)) or before and common_word(before.group(1)))


def names(text, title=False):
    """In a title every word is capitalised, so none is skipped as a sentence start."""
    found = set()
    for line in text.split('\n'):
        for m in NAME.finditer(line):
            if not title and SENTENCE_START.search(line[:m.start()]):
                continue
            if not common_word(m.group(0)) and not compound_part(line, m):
                found.add(m.group(0))
    found.update(n for n in ALWAYS if re.search(r'\b' + re.escape(n) + r'\b', text))
    return found


def names_kept(src, out, title=False):
    for n in names(src, title):
        if n in out:
            continue
        m = re.fullmatch(r'([A-Z][A-Za-z0-9]*?[A-Z0-9][A-Za-z0-9]*?)(e?s)', n)
        if m and m.group(1) in out:      # DReps -> DRep, DEXes -> DEX: Spanish keeps acronyms singular
            continue
        return False
    return True


def looks_spanish(text):
    words = re.findall(r'\w+', text)
    return len(words) >= 8 and len(SPANISH.findall(text)) / len(words) > 0.18


KANA = re.compile(r'[\u3040-\u30ff]')
JAPANESE = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')


def looks_japanese(text):
    return len(JAPANESE.findall(text)) >= 8


def japanese_enough(src, out):
    """A Japanese translation has kana; an abstract is mostly Japanese script."""
    if not KANA.search(out):
        return False
    letters = len(re.findall(r'[A-Za-z]', out)) + len(JAPANESE.findall(out))
    return '\n' not in src.strip() and len(src) < 200 or len(JAPANESE.findall(out)) >= 0.25 * letters

# ---------------------------------------------------------------------------
# What three reviewers found again and again in the machine translations
# (review of 26-09), checked or fixed here, so a new text does not bring the
# same errors back.

# Fixed after the model: terms and names the reviewers corrected throughout.
MONTHS_ES = 'enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre'
AFTER_ES_REVIEW = [
    ('propulsor', 'proponente'),
    ('**Pregunta de la tesorería:**', '**Solicitud a la tesorería:**'),
    ('### Pregunta de Presupuesto Total', '### Solicitud de presupuesto total'),
    ('**Pregunta:**', '**Solicitud:**'), ('Total de preguntas:', 'Solicitud total:'),
    ('Los premios de staking', 'Las recompensas de staking'), ('los premios de staking', 'las recompensas de staking'),
    ('establescoins', 'stablecoins'), ('Valor Total Atado', 'Valor Total Bloqueado'),
    ('La comisión de parámetros', 'El Comité de Parámetros'),
    ('Babel Tarifas', 'Babel Fees'), ('Input Output Investigación', 'Input Output Research'),
    ('DEL ECOSISTEMA DE LA CADENA DE BLOCKCHAIN CARDANO', 'DEL ECOSISTEMA BLOCKCHAIN DE CARDANO'),
    ('cadena blockchain', 'blockchain'), ('titulares de ADA', 'poseedores de ADA'),
    ('intercambios centralizados', 'exchanges centralizados'), ('bifurcación dura', 'hard fork'),
    ('La Fundación Cardano', 'La Cardano Foundation'), ('la Fundación Cardano', 'la Cardano Foundation'),
    ('del Proyecto Catalyst', 'de Project Catalyst'), ('el Proyecto Catalyst', 'Project Catalyst'),
    ('el proyecto Catalyst', 'Project Catalyst'), ('corrientes de trabajo', 'líneas de trabajo'),
    ('Tesorería Cardano', 'Tesorería de Cardano'),
    # 13 de febrero 2026, febrero 13, 2026 -> 13 de febrero de 2026
    (re.compile(rf'\b({MONTHS_ES}) (\d{{1,2}}), (\d{{4}})'), r'\2 de \1 de \3'),
    (re.compile(rf'\b({MONTHS_ES}),? (\d{{4}})'), r'\1 de \2'),
    # y before an i-sound is e; e before anything else is y
    (re.compile(r'(?<=\s)y (?=[hH]?[iíIÍ](?![aeouáéóú]))'), 'e '),
    (re.compile(r'(?<=\s)e (?=[A-Za-zÁÉÓÚáéóúñ])(?![iíIÍ])(?![hH][iíIÍ])'), 'y '),
]
AFTER_JA = [
    # Names stay in Latin letters; the model wrote five spellings of Cardano.
    (re.compile('カーデナノ|カーデノ|カルダノ|カーディノー|カードノー'), 'Cardano'), ('Cardanoー', 'Cardano '),
    (re.compile('ローブレース|ローブラス|ラヴラス|(?<!グ)ローブ'), 'Lovelace'),
    (re.compile(r'Cardano ?ファウンデーション'), 'Cardano Foundation'),
    (re.compile(r'Snek ?ファウンデーション|Snek財団'), 'Snek Foundation'),
    (re.compile(r'Ensurable ?システム'), 'Ensurable Systems'),
    (re.compile('ラボズ|ラボス'), ' Labs'), (re.compile(r'(?<=[a-zA-Z0-9)]) +Labs'), ' Labs'),
    (re.compile('チェンハードフォーク|チェン ハードフォーク'), 'Chang ハードフォーク'),
    # Terms of the glossary.
    ('預金', 'デポジット'), ('監査士', '監査人'), ('責任感', '説明責任'), ('提議', '提案'),
    (re.compile('メモープール|メモプール'), 'メンプール'), (re.compile('満杯度|満たし度'), '飽和度'),
    (re.compile('中心化された取引所|中心化取引所'), '中央集権型取引所'),
    ('交換所', '取引所'), ('安定通貨', 'ステーブルコイン'),
    (re.compile('作業委員会|作業部(?!会)|作業グループ'), 'ワーキンググループ'),
    (re.compile('デシルラライズド|デシラライズド|デセントラライズド'), '分散型'),
    ('ベンダーの代わって', 'ベンダーに代わって'),
    ('**トレジャリーの質問:**', '**トレジャリーへの要請額:**'), ('生産性レベル', '本番環境レベル'),
    # Chinese words and characters in Japanese text.
    ('宪', '憲'), ('资', '資'), ('准備', '準備'), ('端到端', 'エンドツーエンド'),
    ('即用可能な', 'すぐに使える'), ('即用可能', 'すぐに使える'), ('過時した', '古くなった'),
    ('持有者', '保有者'), ('維護', '保守'), ('策略', '戦略'), ('良性循環', '好循環'),
    ('靶向的な', '対象を絞った'), ('靶向的', '対象を絞った'), ('人本設計', '人間中心設計'),
    # Garbled katakana.
    ('テイポ', '誤字'), ('ツールイング', 'ツーリング'), (re.compile('インデックスャー|インデックスラー'), 'インデクサー'),
    ('ガーディレール', 'ガードレール'), ('メンテナントされて', 'メンテナンスされて'),
]


def apply_after(rules, text):
    for pat, rep in rules:
        text = text.replace(pat, rep) if isinstance(pat, str) else pat.sub(rep, text)
    return text


# Amounts with a multiplier. "3 million farmers" came back as 2030 millones
# and 2030 名; "$20 million" as 20 億ドル (two billion). The value must match,
# however it is written: 3 millones, 300万, 3M.
NUM = r'\d(?:[\d,]*\d)?(?:\.\d+)?'
UNIT_EN = {'thousand': 1e3, 'k': 1e3, 'K': 1e3, 'million': 1e6, 'mn': 1e6, 'M': 1e6,
           'billion': 1e9, 'bn': 1e9, 'B': 1e9, 'trillion': 1e12, 'T': 1e12}
UNIT_ES = {'mil millones': 1e9, 'millones': 1e6, 'millón': 1e6, 'billones': 1e12, 'billón': 1e12, 'mil': 1e3,
           'bn': 1e9, 'k': 1e3, 'K': 1e3, 'M': 1e6, 'B': 1e9, 'T': 1e12}
UNIT_JA = {'兆': 1e12, '億': 1e8, '千万': 1e7, '百万': 1e6, '万': 1e4, '千': 1e3}
RANGE = r'(?:\s?[–\-〜～~]\s?)'
# A single letter counts only straight after the number (5M, 10k), never in M1 or 6, M2.
MAG_EN = re.compile(rf'({NUM})(?:{RANGE}({NUM}))?(\s?(?i:thousand|million|billion|trillion)|\s?(?:bn|mn)|[kKMBT])(?![A-Za-z0-9])')
MAG_ES = re.compile(rf'({NUM})(?:{RANGE}({NUM}))?(\s?(?i:mil millones|millones|millón|billones|billón|mil)|\s?bn|[kKMBT])(?![A-Za-z0-9áéíóúñ])')
MAG_JA = re.compile(rf'({NUM})\s?(兆|億|千万|百万|万|千)')


def number(s):
    """1,234.5 or 1,5 (a Spanish decimal comma): a comma before exactly three digits groups thousands."""
    s = re.sub(r',(?=\d{3}(?!\d))', '', s)
    return float(s.replace(',', '.'))


def magnitudes(text, lang):
    """The values of amounts with a multiplier; a range carries its unit to both ends."""
    vals = []
    for pat, units in ((MAG_EN, UNIT_EN),) if lang == 'en' else ((MAG_ES, UNIT_ES),) if lang == 'es' else ((MAG_EN, UNIT_EN),):
        for m in pat.finditer(text):
            w = m.group(3).strip()
            u = units.get(w) or units[w.lower()]
            vals += [number(m.group(1)) * u] + ([number(m.group(2)) * u] if m.group(2) else [])
    if lang == 'ja':
        prev_end, acc = None, 0.0
        for m in MAG_JA.finditer(text):
            v = number(m.group(1)) * UNIT_JA[m.group(2)]
            if prev_end is not None and m.start() == prev_end:
                acc += v              # 1億8,000万 is one amount
                vals[-1] = acc
            else:
                acc = v
                vals.append(v)
                before = re.search(rf'({NUM}){RANGE}$', text[:m.start()])
                if before:            # 10〜20億: the unit belongs to both ends
                    vals.append(number(before.group(1)) * UNIT_JA[m.group(2)])
            prev_end = m.end()
    return vals


def magnitude_spans(src):
    """Where the numbers of amounts with a multiplier are, in the English."""
    spans = []
    for m in MAG_EN.finditer(src):
        spans += [m.span(1)] + ([m.span(2)] if m.group(2) else [])
    return spans


def magnitudes_kept(src, out, lang):
    got = magnitudes(out, lang)
    return all(any(abs(g - v) <= 0.005 * v for g in got) for v in magnitudes(src, 'en'))


# A dollar amount became yen: (0.19ドル/1,868,266円).
# Only after an amount: 円 is also in 楕円 (ellipse) and 円滑 (smooth).
OTHER_CURRENCY = [(re.compile(r'\d\s?円'), ('円', 'yen', 'JPY', '¥')),
                  (re.compile(r'€|\d\s?euros?\b'), ('€', 'EUR', 'euro'))]


def currency_kept(src, out):
    return all(any(s in src for s in sources) for pat, sources in OTHER_CURRENCY if pat.search(out))


# Dates. The Japanese model wrote 13月2026日 and 24 年 2025 月 for
# 13 February 2026 and 24 April 2025.
MONTHS_EN = {m: i + 1 for i, m in enumerate(('january', 'february', 'march', 'april', 'may', 'june', 'july',
                                              'august', 'september', 'october', 'november', 'december'))}
MONTHS_EN.update({m[:3]: i for m, i in list(MONTHS_EN.items())})
MONTHS_EN['sept'] = 9
MON_EN = '|'.join(sorted(MONTHS_EN, key=len, reverse=True))
MON_ES = MONTHS_ES.split('|')
DATE_EN = [re.compile(rf'\b({MON_EN})\.? (\d{{1,2}})(?:st|nd|rd|th)?,? (\d{{4}})\b', re.I),   # month day year
           re.compile(rf'\b(\d{{1,2}})(?:st|nd|rd|th)? ({MON_EN})\.?,? (\d{{4}})\b', re.I),   # day month year
           re.compile(rf'(?<![\d,] )\b({MON_EN})\.?,? (\d{{4}})\b', re.I)]                   # month year


def dates(src):
    found, taken = [], []
    for i, pat in enumerate(DATE_EN):
        for m in pat.finditer(src):
            if any(a <= m.start() < b for a, b in taken):
                continue
            taken.append(m.span())
            g = m.groups()
            if i == 0:
                found.append((int(g[2]), MONTHS_EN[g[0].lower()], int(g[1])))
            elif i == 1:
                found.append((int(g[2]), MONTHS_EN[g[1].lower()], int(g[0])))
            else:
                found.append((int(g[1]), MONTHS_EN[g[0].lower()], None))
    return found


def dates_kept(src, out, lang):
    for y, m, d in dates(src):
        if lang == 'ja':
            ok = (re.search(rf'(?<!\d){m}\s?月\s?{d}\s?日', out) and re.search(rf'{y}\s?年', out)) if d \
                else re.search(rf'{y}\s?年\s?{m}\s?月', out)
        else:
            mes = MON_ES[m - 1]
            ok = (re.search(rf'(?<!\d){d} de {mes}\b', out, re.I) and str(y) in out) if d \
                else re.search(rf'\b{mes},? (?:de |del )?{y}', out, re.I)
        if not ok:
            return False
    return True


# Characters Japanese does not have: the model fell back on simplified Chinese
# (资産, 宪法). What Japanese writes is in the Shift-JIS set (cp932).
HAN = re.compile(r'[㐀-鿿]')


def japanese_script_ok(out):
    for c in set(HAN.findall(out)):
        try:
            c.encode('cp932')
        except UnicodeEncodeError:
            return False
    return True


# A line that comes back as it went in was not translated: nine titles stayed
# English without anyone noticing. Names and links alone may stay as they are.
# In a title, where every word is capitalised, three common words are enough
# (the title then keeps its original wording anyway). A line in an abstract
# needs three common words in lower case, as any English sentence has (the,
# for, with): a line of names (Cardano x Draper Dragon: Orion Fund) has none,
# and must not send the whole abstract back to English.
def untranslated(src, out, title=False):
    if out.strip() != src.strip():
        return False
    text = re.sub(r'https?://\S+|`[^`]*`', ' ', src)
    if title:
        return sum(1 for w in re.findall(r'\b[A-Za-z]{3,}\b', text) if common_word(w)) >= 3
    return sum(1 for w in re.findall(r'\b[a-z]{3,}\b', text) if common_word(w)) >= 3


# Hard line breaks inside a paragraph. The Daedalus abstract has one every
# seventy characters; translated line by line it was unreadable. A line that
# does not end a sentence runs on into the next, unless that one starts a list
# item, a heading, a table row, a quote or code, or ends in a Markdown break.
BLOCK = re.compile(r'^\s*(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|\||>|```)')


def join_wrapped(text):
    out = []
    for line in text.split('\n'):
        prev = out[-1] if out else ''
        if (prev.strip() and line.strip() and not BLOCK.match(line) and not prev.endswith('  ')
                and not re.match(r'^\s*(?:#{1,6}\s|\||```)', prev) and not re.search(r'[.!?:;。！？：]$', prev.rstrip())):
            out[-1] = prev.rstrip() + ' ' + line.strip()
        else:
            out.append(line)
    return '\n'.join(out)


# Paragraphs that recur word for word (the two paragraphs of the Intersect
# proposals) take the reviewed translation, so they read the same everywhere.
def paragraph_memory(data, done):
    mem, clash = {}, set()
    for a in data['actions']:
        r = done.get(a.get('anchor_hash'))
        if not r or not a.get('abstract'):
            continue
        ep, tp = a['abstract'].split('\n\n'), r['abstract'].split('\n\n')
        if len(ep) != len(tp):
            continue
        for e, t in zip(ep, tp):
            e = e.strip()
            if len(e) < 80:
                continue          # headings and short items depend on their context
            if e in mem and mem[e] != t:
                clash.add(e)
            mem.setdefault(e, t)
    for e in clash:
        mem.pop(e)
    return mem


def reuse(src, out, mem):
    ep, op = src.split('\n\n'), out.split('\n\n')
    if not mem or len(ep) != len(op):
        return out
    return '\n\n'.join(mem.get(e.strip(), o) for e, o in zip(ep, op))


LANGS = {
    'es': {'version': VERSION, 'system': SYSTEM, 'examples': EXAMPLES, 'after': AFTER + AFTER_ES_REVIEW,
           'already': looks_spanish, 'enough': None,
           'model': lambda: MODEL_DIR, 'model_env': 'TVOAH_QWEN'},
    'ja': {'version': VERSION_JA, 'system': SYSTEM_JA, 'examples': EXAMPLES_JA, 'after': AFTER_JA,
           'already': looks_japanese, 'enough': japanese_enough,
           'model': lambda: MODEL_DIR, 'model_env': 'TVOAH_QWEN'},
}


def translate_texts(texts, titles=None, lang='es'):
    """Paragraph by paragraph, all texts in one stream so the GPU gets full
    batches: the model sees whole sentences with their context, and each text
    keeps its shape. A text with any paragraph not intact comes back as None."""
    texts = [join_wrapped(t) for t in texts]
    jobs = [(ti, li, line) for ti, text in enumerate(texts)
            for li, line in enumerate(text.split('\n')) if line.strip()]
    titles = titles or [False] * len(texts)
    text_names = [names(text, titles[ti]) for ti, text in enumerate(texts)]
    hidden = [hide_numbers(line, text_names[ti]) for ti, _, line in jobs]
    raw = run_model([h for h, _ in hidden], lang)
    outs = [restore_numbers(line, show_numbers(out, kept)) for (_, _, line), (_, kept), out in zip(jobs, hidden, raw)]
    result = [text.split('\n') for text in texts]
    broken = set()
    for (ti, li, line), out in zip(jobs, outs):
        if not out or not intact(line, out, lang) or untranslated(line, out, titles[ti]):
            broken.add(ti)
        result[ti][li] = re.match(r'[ \t]*', line).group(0) + (out or '').lstrip()   # nested lists keep their depth
    enough = LANGS[lang]['enough']
    return [None if ti in broken or not names_kept(texts[ti], '\n'.join(r), titles[ti])
            or (enough and not enough(texts[ti], '\n'.join(r))) else '\n'.join(r)
            for ti, r in enumerate(result)]


def translate_text(text, lang='es'):
    return translate_texts([text], lang=lang)[0]


def main(path):
    with open(path) as f:
        data = json.load(f)
    os.makedirs(CACHE, exist_ok=True)
    set_prose([x for a in data['actions'] if a.get('title') for x in (a['title'], a['abstract'])])
    langs = os.environ.get('TVOAH_LANGS', 'es').split()
    for a in data['actions']:
        a.pop('i18n', None)
    for lang in langs:
        translate_lang(data, lang)

    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), prefix='.data-', suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def reviewed(lang):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reviewed', f'{lang}.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def translate_lang(data, lang):
    L = LANGS[lang]
    counts = {}
    done = reviewed(lang)
    mem = paragraph_memory(data, done)
    cache_of = lambda a: os.path.join(CACHE, f"{a['anchor_hash']}.{L['version']}.{lang}.json")
    def put(a, tr):
        a.setdefault('i18n', {})[lang] = tr
    todo = []
    for a in data['actions']:
        if not a.get('title') or a.get('title_status') != 'verified':
            continue
        if a['anchor_hash'] in done:
            put(a, dict(done[a['anchor_hash']], model='reviewed'))
            counts['reviewed'] = counts.get('reviewed', 0) + 1
            continue
        if os.path.exists(cache_of(a)):
            with open(cache_of(a)) as f:
                tr = json.load(f)
            if not (names_kept(a['title'], tr['title'], True) and names_kept(a['abstract'], tr['abstract'])
                    and intact(a['title'], tr['title'], lang) and intact(a['abstract'], tr['abstract'], lang)):
                os.remove(cache_of(a))       # made before a check that refuses it now; translate again
                todo.append(a)
                continue
            for key in ('title', 'abstract'):
                tr[key] = apply_after(L['after'], tr[key])
            tr['abstract'] = reuse(a['abstract'], tr['abstract'], mem)
            put(a, tr)
            counts['cached'] = counts.get('cached', 0) + 1
        elif L['already'](a['title'] + ' ' + a['abstract']):
            counts['already_' + lang] = counts.get('already_' + lang, 0) + 1
        elif os.path.exists(cache_of(a) + '.failed'):
            # The model is deterministic: a text that failed the check fails again.
            counts['failed_before'] = counts.get('failed_before', 0) + 1
        elif a['anchor_hash'] not in {b['anchor_hash'] for b in todo}:
            todo.append(a)

    # While another job has the GPU, nothing new is translated: cached
    # translations are used and the rest waits.
    if os.environ.get('TVOAH_TRANSLATE_CACHE_ONLY') and todo:
        counts['deferred'] = len(todo)
        todo = []

    # Ten documents at a time: full GPU batches, and progress is kept in the
    # cache as it goes, so an interrupted run resumes where it stopped.
    for i in range(0, len(todo), 10):
        group = todo[i:i + 10]
        outs = translate_texts([x for a in group for x in (a['title'], a['abstract'])],
                               titles=[x for _ in group for x in (True, False)], lang=lang)
        for k, a in enumerate(group):
            t, ab = outs[2 * k], outs[2 * k + 1]
            # A title that fails a check keeps its original wording: often it is
            # nearly all names (IO: Hydra), and a good abstract is not thrown away for it.
            if t is None and ab is not None:
                t = a['title']
                counts['title_kept'] = counts.get('title_kept', 0) + 1
            if t is None or ab is None:
                counts['not_intact'] = counts.get('not_intact', 0) + 1
                open(cache_of(a) + '.failed', 'w').close()
                continue
            tr = {'title': t, 'abstract': reuse(a['abstract'], ab, mem), 'model': L['version']}
            fd, tmp = tempfile.mkstemp(dir=CACHE)
            with os.fdopen(fd, 'w') as f:
                json.dump(tr, f, ensure_ascii=False)
            os.replace(tmp, cache_of(a))
            counts['translated'] = counts.get('translated', 0) + 1
        print(f'translate {lang}: {min(i + 10, len(todo))} of {len(todo)} documents', flush=True)
    for a in data['actions']:
        if lang not in a.get('i18n', {}) and a.get('anchor_hash') and os.path.exists(cache_of(a)):
            with open(cache_of(a)) as f:
                put(a, json.load(f))
    print(f'translations {lang}:', ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: translate.py DATA.json')
    main(sys.argv[1])
