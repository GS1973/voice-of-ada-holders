#!/usr/bin/env python3
"""The Voice of ADA Holders: machine translation of proposal texts.

Translates each verified title and abstract from English to Spanish, and to
Japanese when asked, with Qwen3 on ctranslate2, local on the GPU (CPU
fallback): Spanish with the 4B model in TVOAH_QWEN, Japanese with the 8B model
in TVOAH_QWEN_JA (the 4B model dropped amounts and wrote Cyrillic in Japanese).
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
"""
import json
import os
import re
import sys
import tempfile

MODEL_DIR = os.path.expanduser(os.environ.get('TVOAH_QWEN', ''))   # required unless cache-only
MODEL_DIR_JA = os.path.expanduser(os.environ.get('TVOAH_QWEN_JA', ''))
CACHE = os.path.expanduser(os.environ.get('TVOAH_TRANSLATIONS', '~/.cache/tvoah/translations'))
VERSION = 'qwen3-4b-int8-2'   # part of the Spanish cache key: change the prompt, change this
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
Constitutional Committee -> Comité Constitucional; delegator -> delegador; on-chain -> en la cadena; hard fork -> hard fork.

Write natural, correct Spanish: agreement and word order follow Spanish grammar, not the English original."""

# The examples carry placeholders, never real amounts: with an amount in an
# example the model once filled a hidden 5,000,000 with this example's 11,787,063.
EXAMPLES = [
    ("Reduce minPoolCost to {{N0}} ada",
     "Reducir minPoolCost a {{N0}} ada"),
    ("Withdraw {{N0}} ada for the OpenZeppelin Stack administered by Intersect",
     "Retirar {{N0}} ada para el OpenZeppelin Stack administrado por Intersect"),
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
KEEP = re.compile(r'`[^`\n]+`|https?://[^\s)\]]*[^\s)\].,;:]|' + BECH32 + r'|\b[0-9a-f]{16,}\b|₳\s?\d[\d,.]*\d|\d[\d,.]*\d')

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
AFTER = [(re.compile(r'\bestake'), 'stake'), (re.compile(r'\bEstake'), 'Stake')]   # also estakeados

# Numbers and links are taken out before the model sees them and put back after.
# Left in, the model changed them: Epoch 713 became 710, a link to
# explorer.cardano.org became explorer.cardcardano.org, and 11,787,063 ada
# became 11,787,065. A single digit stays in, for the grammar.
HIDE = re.compile(r'(?P<L>https?://[^\s)\]]*[^\s)\].,;:]|' + BECH32 + r')|(?P<N>₳\s?\d[\d,.]*\d|\d[\d,.]*\d)')
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
            for pat, rep_ in LANGS[lang]['after']:
                o = pat.sub(rep_, o)
            outs.append(o)
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


def intact(src, out):
    """Every number, link, code span and hash of the original is in the
    translation, and no letters of a foreign script were added."""
    return (all(kept(k, out) for k in KEEP.findall(src)) and '{{' not in out
            and all(c in src for c in FOREIGN.findall(out)))


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


LANGS = {
    'es': {'version': VERSION, 'system': SYSTEM, 'examples': EXAMPLES, 'after': AFTER,
           'already': looks_spanish, 'enough': None,
           'model': lambda: MODEL_DIR, 'model_env': 'TVOAH_QWEN'},
    'ja': {'version': VERSION_JA, 'system': SYSTEM_JA, 'examples': EXAMPLES_JA, 'after': [],
           'already': looks_japanese, 'enough': japanese_enough,
           'model': lambda: MODEL_DIR_JA, 'model_env': 'TVOAH_QWEN_JA'},
}


def translate_texts(texts, titles=None, lang='es'):
    """Paragraph by paragraph, all texts in one stream so the GPU gets full
    batches: the model sees whole sentences with their context, and each text
    keeps its shape. A text with any paragraph not intact comes back as None."""
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
        if not out or not intact(line, out):
            broken.add(ti)
        result[ti][li] = out
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


def translate_lang(data, lang):
    L = LANGS[lang]
    counts = {}
    cache_of = lambda a: os.path.join(CACHE, f"{a['anchor_hash']}.{L['version']}.{lang}.json")
    def put(a, tr):
        a.setdefault('i18n', {})[lang] = tr
    todo = []
    for a in data['actions']:
        if not a.get('title') or a.get('title_status') != 'verified':
            continue
        if os.path.exists(cache_of(a)):
            with open(cache_of(a)) as f:
                tr = json.load(f)
            if not (names_kept(a['title'], tr['title'], True) and names_kept(a['abstract'], tr['abstract'])
                    and intact(a['title'], tr['title']) and intact(a['abstract'], tr['abstract'])):
                os.remove(cache_of(a))       # made before a check that refuses it now; translate again
                todo.append(a)
                continue
            for key in ('title', 'abstract'):
                for pat, rep_ in L['after']:
                    tr[key] = pat.sub(rep_, tr[key])
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
            if t is None or ab is None:
                counts['not_intact'] = counts.get('not_intact', 0) + 1
                open(cache_of(a) + '.failed', 'w').close()
                continue
            tr = {'title': t, 'abstract': ab, 'model': L['version']}
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
