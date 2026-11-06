#!/usr/bin/env python3
"""Find and download public-domain images from Wikimedia Commons, with the licence checked first.

  fetch_commons_image.py --search "Botticelli Birth of Venus"          # list candidates with licences
  fetch_commons_image.py "File:Some Name.jpg" --out img/venus.jpg      # download (refuses non-public-domain)

Accepted: licences whose short name starts with "Public domain", "PD" or "CC0". Anything else (CC BY, CC BY-SA,
fair use, unknown) is refused with the licence printed, because the guide page has no per-image credit line.
Photographs of 3-D works, modern buildings and people are usually copyrighted by the photographer even when the
object is old: check the licence line, not just the subject. Appends a line to img/CREDITS.tsv for the record.
Needs internet; Pillow is used to convert PNG/TIFF to JPEG when installed.
"""
import argparse, io, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

API = 'https://commons.wikimedia.org/w/api.php'
UA = 'audio-guide-builder/1.0 (Claude Code skill; public-domain image fetch)'
OK_LICENSE = re.compile(r'^(public domain|pd\b|pd-|cc0)', re.I)


def open_url(req, timeout):
    """urlopen with back-off: Wikimedia answers 429 when requests come too fast."""
    last = None
    for attempt in range(5):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 503):
                break
            wait = int(e.headers.get('Retry-After') or 0) or 2 * 2 ** attempt
            time.sleep(min(wait, 30))
        except urllib.error.URLError as e:
            last = e
            time.sleep(2 * (attempt + 1))
    sys.exit('Commons request failed (%s). Wait a minute and retry, and keep to a few requests at a time.' % last)


def api(**params):
    params.update(format='json', formatversion='2')
    req = urllib.request.Request(API + '?' + urllib.parse.urlencode(params), headers={'User-Agent': UA})
    with open_url(req, 30) as r:
        return json.load(r)


def info(title, width):
    d = api(action='query', titles=title, prop='imageinfo', iiprop='url|extmetadata|mime|size', iiurlwidth=width, redirects=1)
    page = d['query']['pages'][0]
    if 'imageinfo' not in page:
        sys.exit('not found on Commons: %s' % title)
    return page['title'], page['imageinfo'][0]


def licence_of(ii):
    em = ii.get('extmetadata', {})
    return (em.get('LicenseShortName', {}).get('value') or em.get('UsageTerms', {}).get('value') or 'unknown').strip()


def search(q):
    d = api(action='query', list='search', srsearch=q + ' filetype:bitmap', srnamespace=6, srlimit=8)
    for hit in d['query']['search']:
        try:
            title, ii = info(hit['title'], 300)
        except SystemExit:
            continue
        lic = licence_of(ii)
        print('%-4s %-26s %5dx%-5d %s' % ('PD' if OK_LICENSE.match(lic) else 'NO', lic[:26], ii['width'], ii['height'], title))


def fetch(title, out, width):
    title, ii = info(title if title.startswith('File:') else 'File:' + title, width)
    lic = licence_of(ii)
    if not OK_LICENSE.match(lic):
        sys.exit('refused: licence is "%s", not public domain / CC0 (%s)' % (lic, ii['descriptionurl']))
    url = ii.get('thumburl') or ii['url']
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with open_url(req, 60) as r:
        raw = r.read()
    if not raw[:3] == b'\xff\xd8\xff':
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(raw)).convert('RGB')
            buf = io.BytesIO()
            im.save(buf, 'JPEG', quality=85, optimize=True)
            raw = buf.getvalue()
        except ImportError:
            sys.exit('the file is not a JPEG and Pillow is not installed to convert it')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'wb').write(raw)
    with open(os.path.join(os.path.dirname(os.path.abspath(out)), 'CREDITS.tsv'), 'a', encoding='utf-8') as f:
        f.write('%s\t%s\t%s\t%s\n' % (os.path.basename(out), title, lic, ii['descriptionurl']))
    print('saved %s (%d KB) | %s | %s' % (out, len(raw) // 1024, lic, ii['descriptionurl']))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('title', nargs='?', help='Commons file title, e.g. "File:Name.jpg"')
    ap.add_argument('--out', help='where to save (e.g. img/<id>.jpg)')
    ap.add_argument('--width', type=int, default=760)
    ap.add_argument('--search')
    a = ap.parse_args()
    if a.search:
        search(a.search)
    elif a.title and a.out:
        fetch(a.title, a.out, a.width)
    else:
        ap.error('give --search "query", or a file title with --out')


if __name__ == '__main__':
    main()
