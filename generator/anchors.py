#!/usr/bin/env python3
"""The Voice of ADA Holders — proposal documents.

Every governance action carries an anchor on chain: a URL and the blake2b-256
hash of the document behind it. This step fetches each document, keeps it only
if its bytes hash to the value on chain, and takes the title and abstract from
it (CIP-108). A document that cannot be fetched or does not match gives no
title, and data.json says why.

db-sync is deliberately on-chain only (offchain_vote_data disabled), so this
is done here and not there.

    anchors.py DATA.json          (rewrites DATA.json in place)

Verified documents are cached by their hash in $TVOAH_CACHE (default
~/.cache/tvoah/anchors): a document that matched once never has to be fetched
again, because the chain fixes its bytes.
"""
import hashlib
import ipaddress
import json
import os
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

# Any gateway will do: the hash on chain decides whether the bytes are right.
# Public gateways rate-limit, so requests are paced and each gateway is tried in turn.
IPFS_GATEWAYS = os.environ.get('TVOAH_IPFS_GATEWAYS', 'https://gateway.pinata.cloud/ipfs/ https://w3s.link/ipfs/ https://4everland.io/ipfs/ https://ipfs.io/ipfs/ https://dweb.link/ipfs/').split()
PACE = 2.0  # seconds between requests
CACHE = os.path.expanduser(os.environ.get('TVOAH_CACHE', '~/.cache/tvoah/anchors'))
MAX_BYTES = 2 * 1024 * 1024
TIMEOUT = 20


def blake2b_256(b):
    return hashlib.blake2b(b, digest_size=32).hexdigest()


def public_host(host):
    """Refuse anchors that point into a private network. urllib resolves the
    name again when it connects, so a name that changes its answer in between
    could still reach an internal address; accepted (25-09-2026): only https
    is fetched, and the certificate must be valid for the public name, which
    an internal service does not have, so no bytes come back from it."""
    try:
        infos = socket.getaddrinfo(host, 443)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


class _Redirects(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to another public https address."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme != 'https' or not public_host(p.hostname or ''):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_Redirects)


def get(url):
    """One https request. Return (bytes, None) or (None, reason)."""
    parts = urllib.parse.urlparse(url)
    if parts.scheme != 'https':
        return None, 'not_https'
    if not public_host(parts.hostname or ''):
        return None, 'unreachable'
    time.sleep(PACE)
    req = urllib.request.Request(url, headers={'User-Agent': 'the-voice-of-ada-holders/1'})
    try:
        with _opener.open(req, timeout=TIMEOUT) as r:
            body = r.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        return None, 'rate_limited' if e.code == 429 else 'unreachable'
    except Exception:
        return None, 'unreachable'
    if len(body) > MAX_BYTES:
        return None, 'too_large'
    return body, None


def candidates(url):
    """The anchor URL itself, then every gateway for an IPFS content id."""
    cid = None
    if url.startswith('ipfs://'):
        cid = url[len('ipfs://'):]
    else:
        path = urllib.parse.urlparse(url).path
        if '/ipfs/' in path:
            cid = path.split('/ipfs/', 1)[1]
        yield url
    if cid:
        for g in IPFS_GATEWAYS:
            yield g + cid


def fetch(url, want_hash):
    """Try each candidate until one returns bytes with the hash on chain.
    Return (bytes, None) or (None, reason of the last attempt, mismatch first)."""
    reason = 'unreachable'
    for u in candidates(url):
        body, why = get(u)
        if body is None:
            reason = why if reason != 'hash_mismatch' else reason
            continue
        if blake2b_256(body) == want_hash:
            return body, None
        reason = 'hash_mismatch'
    return None, reason


def text_of(v):
    """CIP-108 fields are plain strings or JSON-LD values ({"@value": ...})."""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, dict) and isinstance(v.get('@value'), str):
        return v['@value'].strip()
    return ''


RETRY_AFTER = 6 * 3600   # a document that could not be had is tried again after this


def document(url, want_hash):
    """Return (doc_json, status). status: verified | hash_mismatch | not_json |
    unreachable | rate_limited | not_https | too_large."""
    cached = os.path.join(CACHE, want_hash + '.json')
    if os.path.exists(cached):
        with open(cached, 'rb') as f:
            body = f.read()
    else:
        failed = os.path.join(CACHE, want_hash + '.failed')
        if os.path.exists(failed) and time.time() - os.path.getmtime(failed) < RETRY_AFTER:
            with open(failed) as f:
                return None, f.read().strip() or 'unreachable'
        body, reason = fetch(url, want_hash)
        if body is None:
            os.makedirs(CACHE, exist_ok=True)
            with open(failed, 'w') as f:
                f.write(reason)
            return None, reason
        os.makedirs(CACHE, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=CACHE)
        with os.fdopen(fd, 'wb') as f:
            f.write(body)
        os.replace(tmp, cached)
    try:
        return json.loads(body.decode('utf-8')), 'verified'
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, 'not_json'


def main(path):
    with open(path) as f:
        data = json.load(f)
    counts = {}
    for a in data['actions']:
        a['title'], a['abstract'] = '', ''
        url, want = a.get('anchor_url'), a.get('anchor_hash')
        if not url or not want:
            status = 'no_anchor'
        else:
            # One document must not stop the others, nor the tally behind them.
            try:
                doc, status = document(url, want)
            except Exception as e:
                print(f'document {want}: {e!r}')
                doc, status = None, 'unreachable'
            if doc is not None:
                body = doc.get('body') if isinstance(doc.get('body'), dict) else {}
                a['title'] = text_of(body.get('title'))[:300]
                a['abstract'] = text_of(body.get('abstract'))[:5000]
                if not a['title']:
                    status = 'no_title'
        a['title_status'] = status
        counts[status] = counts.get(status, 0) + 1

    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), prefix='.data-', suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)
    print('documents:', ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: anchors.py DATA.json')
    main(sys.argv[1])
