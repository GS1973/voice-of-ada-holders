#!/usr/bin/env python3
"""The Voice of ADA Holders: Spanish machine translation of proposal texts.

Translates each verified title and abstract from English to Spanish with
Qwen3-4B, int8, on ctranslate2 (the directory in TVOAH_QWEN), local on the GPU
(CPU fallback).
No outside service. Translations are cached by the document's on-chain hash,
so each document is translated once. The site marks them as machine
translation and always offers the original.

    translate.py DATA.json        (adds action.i18n.es = {title, abstract})

A language model can be told what not to touch, so names, numbers, code and
Cardano terms are handled in the prompt, not by placeholders (placeholders broke
the grammar around them). What the prompt cannot guarantee is checked after:
every number, link and code span of the original must come back unchanged, or
the text stays in English.
"""
import json
import os
import re
import sys
import tempfile

MODEL_DIR = os.path.expanduser(os.environ.get('TVOAH_QWEN', ''))   # required unless cache-only
CACHE = os.path.expanduser(os.environ.get('TVOAH_TRANSLATIONS', '~/.cache/tvoah/translations'))
VERSION = 'qwen3-4b-int8-2'   # part of the cache key: change the prompt, change this
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

# What must survive the translation unchanged. A single digit may come back as
# a word (4 weeks -> cuatro semanas); a link ends before a closing bracket or
# trailing punctuation.
KEEP = re.compile(r'`[^`\n]+`|https?://[^\s)\]]*[^\s)\].,;:]|\b[0-9a-f]{16,}\b|\d[\d,.]*\d')

SPANISH = re.compile(r'\b(el|la|los|las|de|que|y|en|para|por|una|con|del|se)\b', re.I)

_engine = None


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


def engine():
    global _engine
    if _engine is None:
        if not MODEL_DIR:
            raise SystemExit("translate: set TVOAH_QWEN to the model directory")
        cuda_libs()
        import ctranslate2
        from tokenizers import Tokenizer
        tok = Tokenizer.from_file(os.path.join(MODEL_DIR, 'tokenizer.json'))
        try:
            gen = ctranslate2.Generator(MODEL_DIR, device='cuda', compute_type='int8_float16')
        except Exception as exc:
            print(f'translate: cuda unavailable ({exc}); using CPU')
            gen = ctranslate2.Generator(MODEL_DIR, device='cpu', compute_type='int8')
        _engine = (tok, gen)
    return _engine


def prompt(text):
    p = f"<|im_start|>system\n{SYSTEM}<|im_end|>\n"
    for en, es in EXAMPLES:
        p += f"<|im_start|>user\n{en}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n{es}<|im_end|>\n"
    return p + f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


# Fixed after the model, because it keeps writing them despite the prompt.
AFTER = [(re.compile(r'\bestake'), 'stake'), (re.compile(r'\bEstake'), 'Stake')]   # also estakeados

# Numbers and links are taken out before the model sees them and put back after.
# Left in, the model changed them: Epoch 713 became 710, a link to
# explorer.cardano.org became explorer.cardcardano.org, and 11,787,063 ada
# became 11,787,065. A single digit stays in, for the grammar.
HIDE = re.compile(r'(?P<L>https?://[^\s)\]]*[^\s)\].,;:])|(?P<N>\d[\d,.]*\d)')
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


def run_model(texts):
    """Translate many paragraphs in batches. Each may produce at most about twice
    its own length, so one runaway answer cannot hold a whole batch."""
    tok, gen = engine()
    outs = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        batch = [tok.encode(prompt(t), add_special_tokens=False).tokens for t in chunk]
        limit = min(MAX_TOKENS, 2 * max(len(tok.encode(t).ids) for t in chunk) + 64)
        res = gen.generate_batch(batch, max_length=limit, sampling_temperature=0.0,
                                 include_prompt_in_result=False, end_token=['<|im_end|>'])
        # Decode ids, not token strings: joined strings mangle accents.
        for r in res:
            o = tok.decode(r.sequences_ids[0], skip_special_tokens=True)
            o = re.sub(r'<think>.*?</think>', '', o, flags=re.S).strip()
            for pat, rep_ in AFTER:
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


def intact(src, out):
    """Every number, link, code span and hash of the original is in the translation."""
    return all(k in out for k in KEEP.findall(src)) and '{{' not in out


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


def names(text, title=False):
    """In a title every word is capitalised, so none is skipped as a sentence start."""
    found = set()
    for line in text.split('\n'):
        for m in NAME.finditer(line):
            if not title and SENTENCE_START.search(line[:m.start()]):
                continue
            if not common_word(m.group(0)):
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


def translate_texts(texts, titles=None):
    """Paragraph by paragraph, all texts in one stream so the GPU gets full
    batches: the model sees whole sentences with their context, and each text
    keeps its shape. A text with any paragraph not intact comes back as None."""
    jobs = [(ti, li, line) for ti, text in enumerate(texts)
            for li, line in enumerate(text.split('\n')) if line.strip()]
    titles = titles or [False] * len(texts)
    text_names = [names(text, titles[ti]) for ti, text in enumerate(texts)]
    hidden = [hide_numbers(line, text_names[ti]) for ti, _, line in jobs]
    raw = run_model([h for h, _ in hidden])
    outs = [restore_numbers(line, show_numbers(out, kept)) for (_, _, line), (_, kept), out in zip(jobs, hidden, raw)]
    result = [text.split('\n') for text in texts]
    broken = set()
    for (ti, li, line), out in zip(jobs, outs):
        if not out or not intact(line, out):
            broken.add(ti)
        result[ti][li] = out
    return [None if ti in broken or not names_kept(texts[ti], '\n'.join(r), titles[ti]) else '\n'.join(r)
            for ti, r in enumerate(result)]


def translate_text(text):
    return translate_texts([text])[0]


def main(path):
    with open(path) as f:
        data = json.load(f)
    os.makedirs(CACHE, exist_ok=True)
    set_prose([x for a in data['actions'] if a.get('title') for x in (a['title'], a['abstract'])])
    counts = {}
    cache_of = lambda a: os.path.join(CACHE, f"{a['anchor_hash']}.{VERSION}.es.json")
    todo = []
    for a in data['actions']:
        a.pop('i18n', None)
        if not a.get('title') or a.get('title_status') != 'verified':
            continue
        if os.path.exists(cache_of(a)):
            with open(cache_of(a)) as f:
                es = json.load(f)
            if not (names_kept(a['title'], es['title'], True) and names_kept(a['abstract'], es['abstract'])):
                os.remove(cache_of(a))       # made before the name check; translate again
                todo.append(a)
                continue
            for key in ('title', 'abstract'):
                for pat, rep_ in AFTER:
                    es[key] = pat.sub(rep_, es[key])
            a['i18n'] = {'es': es}
            counts['cached'] = counts.get('cached', 0) + 1
        elif looks_spanish(a['title'] + ' ' + a['abstract']):
            counts['already_spanish'] = counts.get('already_spanish', 0) + 1
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
                               titles=[x for _ in group for x in (True, False)])
        for k, a in enumerate(group):
            t, ab = outs[2 * k], outs[2 * k + 1]
            if t is None or ab is None:
                counts['not_intact'] = counts.get('not_intact', 0) + 1
                open(cache_of(a) + '.failed', 'w').close()
                continue
            es = {'title': t, 'abstract': ab, 'model': VERSION}
            fd, tmp = tempfile.mkstemp(dir=CACHE)
            with os.fdopen(fd, 'w') as f:
                json.dump(es, f, ensure_ascii=False)
            os.replace(tmp, cache_of(a))
            counts['translated'] = counts.get('translated', 0) + 1
        print(f'translate: {min(i + 10, len(todo))} of {len(todo)} documents', flush=True)
    for a in data['actions']:
        if 'i18n' not in a and a.get('anchor_hash') and os.path.exists(cache_of(a)):
            with open(cache_of(a)) as f:
                a['i18n'] = {'es': json.load(f)}

    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), prefix='.data-', suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)
    print('translations:', ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: translate.py DATA.json')
    main(sys.argv[1])
