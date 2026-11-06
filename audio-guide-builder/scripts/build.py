#!/usr/bin/env python3
"""Build an audio guide from a project folder.

  python3 build.py [--project DIR] [--max-level N]

Reads   <project>/guide.json, <project>/content/*.md, <project>/img/*, <project>/audio/manifest.json
Writes  <project>/items.json         parsed content (the recording step reads this)
        <project>/standalone.html    the whole guide in one file, device voice only (no audio files)
        <project>/dist/index.html    the page, wired to the recorded narration
        <project>/dist/a/*.mp3       the recordings listed in the manifest

Everything language-specific comes from assets/lang/<code>.json and assets/ui/<code>.json (see lang.py).
Content format and guide.json fields are documented in references/format.md.
"""
import argparse, base64, glob, html, io, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402

TEMPLATE = os.path.join(L.SKILL_DIR, 'assets', 'template.html')
WARN = []


def warn(msg):
    WARN.append(msg)


def die(msg):
    sys.exit('build.py: ' + msg)


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project', default='.', help='project folder holding guide.json (default: current folder)')
    ap.add_argument('--max-level', type=int, default=None, help='only ship audio for levels <= N (debugging)')
    return ap.parse_args()


def load_config(root):
    p = os.path.join(root, 'guide.json')
    if not os.path.exists(p):
        die('no guide.json in %s (copy assets/examples/guide.en.json to start)' % root)
    cfg = json.load(open(p, encoding='utf-8'))
    for k in ('title', 'language', 'sites'):
        if not cfg.get(k):
            die('guide.json needs "%s"' % k)
    seen = set()
    for s in cfg['sites']:
        for k in ('id', 'name'):
            if not s.get(k):
                die('every site needs "%s": %r' % (k, s))
        if s['id'] in seen or s['id'].startswith('s-'):
            die('duplicate or reserved site id: %s' % s['id'])
        seen.add(s['id'])
    return cfg


# ------------------------------------------------------------------ content parsing

def parse_content(root, cfg, lang, ui):
    first_site = cfg['sites'][0]['id']
    join = lang['split'].get('join_lines', '')
    items = []
    files = sorted(glob.glob(os.path.join(root, 'content', '*.md')))
    if not files:
        die('no content/*.md files in %s' % root)
    for f in files:
        txt = open(f, encoding='utf-8').read()
        for blk in re.split(r'^@@ ', txt, flags=re.M)[1:]:
            lines = blk.split('\n')
            it = {'id': lines[0].strip(), 'sections': [], 'src': [], '_file': os.path.basename(f)}
            it['_seq'] = len(items)
            i = 1
            while i < len(lines) and not lines[i].startswith('## '):
                m = re.match(r'^([a-z_]+):\s?(.*)$', lines[i])
                if m:
                    it[m.group(1)] = m.group(2).strip()
                i += 1
            for alias, real in (('lat', 'orig'), ('by', 'artist')):
                if alias in it and real not in it:
                    it[real] = it.pop(alias)
            cur, buf = None, []

            def flush():
                nonlocal cur, buf
                if cur is None:
                    return
                paras = [b.strip() for b in '\n'.join(buf).split('\n\n') if b.strip()]
                cur['paras'] = [L.split_sentences(p.replace('\n', join), lang) for p in paras]
                it['sections'].append(cur)
                cur, buf = None, []

            for ln in lines[i:]:
                if ln.startswith('## '):
                    flush()
                    m = re.match(r'^## (\d) \| (.*)$', ln)
                    if not m:
                        die('%s: bad section line %r (expected "## <level> | <heading>")' % (it['id'], ln))
                    cur = {'lv': int(m.group(1)), 'h': m.group(2).strip()}
                    buf = []
                elif ln.startswith('@src '):
                    if ' | ' not in ln:
                        die('%s: @src needs "title | url"' % it['id'])
                    t, u = ln[5:].split(' | ', 1)
                    it['src'].append({'t': t.strip(), 'u': u.strip()})
                else:
                    buf.append(ln)
            flush()
            if not it['sections']:
                die('%s has no sections' % it['id'])
            look = [x.strip() for x in it.pop('look', '').split(' | ') if x.strip()]
            if look:
                lv1 = [k for k, s in enumerate(it['sections']) if s['lv'] == 1]
                if not lv1:
                    die('%s has a look: list but no level-1 section to attach it to' % it['id'])
                it['sections'].insert(lv1[-1] + 1, {'lv': 1, 'h': it.pop('lookhead', ui['look_heading']), 'list': look})
            it.setdefault('site', first_site)
            it['img_name'] = it.pop('img', '')
            items.append(it)
    return items


def finish_items(items, cfg, nl):
    sites_by = {s['id']: s for s in cfg['sites']}
    seen = set()
    for it in items:
        if it['id'] in seen:
            die('duplicate item id %s' % it['id'])
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', it['id']) or it['id'].startswith('s-'):
            die('item id %r must be lower-case letters, digits and hyphens, and must not start with "s-"' % it['id'])
        seen.add(it['id'])
        if it['site'] not in sites_by:
            die('%s: unknown site %r (guide.json sites: %s)' % (it['id'], it['site'], ', '.join(sites_by)))
        if not it.get('title'):
            die('%s needs a title:' % it['id'])
        for s in it['sections']:
            if not 1 <= s['lv'] <= nl:
                die('%s: section level %d outside 1..%d (guide.json levels)' % (it['id'], s['lv'], nl))
        it['_ord'] = int(it['ord']) if it.get('ord') else it['_seq'] * 10
        it.pop('ord', None)
        site = sites_by[it['site']]
        if site.get('auto_src') and not it.pop('nosrc', None):
            it['src'].append(site['auto_src'])
        it.pop('nosrc', None)
    order = {s['id']: k for k, s in enumerate(cfg['sites'])}
    items.sort(key=lambda it: (order[it['site']], it['_ord'], it['_seq']))
    for it in items:
        it.pop('_ord')
        it.pop('_seq')
    sites = []
    for s in cfg['sites']:
        s = dict(s)
        s.pop('auto_src', None)
        s['ids'] = [it['id'] for it in items if it['site'] == s['id']]
        if not s['ids']:
            die('site %s has no items' % s['id'])
        s.setdefault('native', '')
        s.setdefault('kind', '')
        s.setdefault('when', '')
        s.setdefault('blurb', '')
        s.setdefault('note', '')
        s.setdefault('foot', '')
        s.setdefault('links', [])
        s.setdefault('mark', (re.sub(r'[^A-Za-z]', '', s['name'])[:2].capitalize() or s['name'][:1]))
        s['groups'] = []
        names = []
        for it in [i for i in items if i['site'] == s['id']]:
            g = it.get('group', '')
            if not s['groups'] or s['groups'][-1]['name'] != g:
                if g and g in names:
                    die('site %s: group %r is split into two runs; give its items consecutive ord: values' % (s['id'], g))
                s['groups'].append({'name': g, 'ids': []})
                names.append(g)
            s['groups'][-1]['ids'].append(it['id'])
        sites.append(s)
    return sites


# ------------------------------------------------------------------ images

def load_images(root, items):
    img, th = {}, {}
    wanted = [it for it in items if it['img_name']]
    if not wanted:
        for it in items:
            it.pop('img_name')
        return img, th
    try:
        from PIL import Image
    except ImportError:
        die('Pillow is needed for images: pip install pillow (or remove img: lines)')
    for it in items:
        n = it.pop('img_name')
        if not n:
            continue
        path = next((p for p in (os.path.join(root, 'img', n + e) for e in ('.jpg', '.jpeg', '.png')) if os.path.exists(p)), None)
        if not path:
            warn('missing image %r for %s' % (n, it['id']))
            continue
        raw = open(path, 'rb').read()
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        if len(raw) > 350_000 or max(im.size) > 1000 or not path.lower().endswith(('.jpg', '.jpeg')):
            big = im.copy()
            big.thumbnail((900, 900), Image.LANCZOS)
            b = io.BytesIO()
            big.save(b, 'JPEG', quality=82, optimize=True)
            raw = b.getvalue()
        img[it['id']] = 'data:image/jpeg;base64,' + base64.b64encode(raw).decode()
        im.thumbnail((220, 220), Image.LANCZOS)
        b = io.BytesIO()
        im.save(b, 'JPEG', quality=72, optimize=True)
        th[it['id']] = 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
    return img, th


# ------------------------------------------------------------------ audio

def js_chars(it, level):
    """Characters of one level, counted like the page's chars()."""
    n = 0
    for s in it['sections']:
        if s['lv'] != level:
            continue
        n += len(s['h'])
        if 'list' in s:
            n += sum(len(x) + 3 for x in s['list'])
        else:
            n += sum(len(x) for p in s['paras'] for x in p)
    return n


def attach_audio(root, items, max_level):
    man_path = os.path.join(root, 'audio', 'manifest.json')
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    files, chars, secs, tracks = [], 0, 0.0, 0
    by_id = {it['id']: it for it in items}
    for iid in man:
        if iid not in by_id:
            warn('audio manifest has %r but no such item (stale recording?)' % iid)
    for it in items:
        a = man.get(it['id'])
        if not a:
            continue
        lv = {}
        for lvl, v in a.items():
            if max_level and int(lvl) > max_level:
                continue
            if not os.path.exists(os.path.join(root, 'audio', v['f'])):
                warn('manifest lists %s but the file is missing' % v['f'])
                continue
            expected = L.unit_count(it, int(lvl))
            if expected != len(v['t']):
                warn('%s level %s: text has %d units but the recording has %d. Re-record it (text changed after recording).'
                     % (it['id'], lvl, expected, len(v['t'])))
            lv[lvl] = {'f': v['f'], 't': v['t']}
            files.append(v['f'])
            chars += js_chars(it, int(lvl))
            secs += v['d']
            tracks += 1
        if lv:
            it['aud'] = lv
    cps = round(chars / secs, 2) if tracks >= 3 and secs > 0 else None
    return files, cps


# ------------------------------------------------------------------ lint

def lint(items, lang, cfg):
    cjk = lang['split']['mode'] == 'cjk'
    longest = 120 if cjk else 260
    for it in items:
        if not it['src'] and not any(s.get('auto_src') for s in cfg['sites'] if s['id'] == it['site']):
            warn('%s has no @src lines. Every factual stop should list the sources actually read.' % it['id'])
        levels = {s['lv'] for s in it['sections']}
        if 1 in levels and any(l not in levels for l in range(1, max(levels) + 1)):
            warn('%s skips a level (has %s)' % (it['id'], sorted(levels)))
        for s in it['sections']:
            texts = s['list'] if 'list' in s else [x for p in s['paras'] for x in p]
            for t in texts:
                if len(t) > longest:
                    warn('%s: a %d-character sentence reads poorly aloud: %s...' % (it['id'], len(t), t[:50]))
                if re.search(r'\b(TODO|TBD|FIXME|XXX)\b|lorem ipsum', t, re.I):
                    warn('%s: placeholder text left in narration: %s' % (it['id'], t[:50]))


# ------------------------------------------------------------------ page assembly

def render(tpl, data, ui, extra):
    vals = dict(extra)

    def sub(m):
        raw, key = m.group(1), m.group(2)
        if key.startswith('ui.'):
            v = ui[key[3:]]
        else:
            v = vals[key]
        return v if raw else html.escape(v, quote=True)

    out = re.sub(r'\{\{(raw:)?([A-Za-z_.]+)\}\}', sub, tpl)
    if not vals.get('font_google'):                       # no web fonts requested: drop the Google Fonts links
        out = re.sub(r'<link[^>]*fonts\.(?:googleapis|gstatic)\.com[^>]*>\n?', '', out)
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/').replace('<!--', '<\\!--')
    assert '/*DATA*/' in out
    out = out.replace('/*DATA*/', js)
    left = re.findall(r'\{\{[^}]*\}\}', out)
    if left:
        die('unresolved template tokens: %s' % left[:5])
    return out


def main():
    args = parse_args()
    root = os.path.abspath(args.project)
    cfg = load_config(root)
    code = cfg['language']
    lang = L.load_lang(code, cfg.get('lang'))
    if lang.get('_generic') and not cfg.get('lang'):
        warn('no shipped language file for %r; using the generic template. Add a "lang" block to guide.json '
             '(ordinals, abbreviations, number-range word, voice locale); see references/languages.md.' % code)
    ui_code = cfg.get('ui_language') or code          # the page can be in a different language than the narration
    ui, missing = L.load_ui(ui_code, root, cfg.get('ui'))
    if missing:
        warn('UI translation for %r is %s; the missing strings will show in English. Add %s/ui.%s.json (copy assets/ui/en.json and translate).'
             % (ui_code, 'absent' if missing == ['*'] else 'missing %d strings (%s...)' % (len(missing), ', '.join(missing[:4])), root, ui_code.split('-')[0]))
    levels = cfg.get('levels') or ui['levels']
    if not 1 <= len(levels) <= 3:
        die('"levels" needs 1 to 3 entries')
    nl = len(levels)
    vc = lang.setdefault('voice', {})
    if not vc.get('lang_re'):
        vc['lang_re'] = '^' + code.split('-')[0]

    items = parse_content(root, cfg, lang, ui)
    sites = finish_items(items, cfg, nl)
    json.dump(items, open(os.path.join(root, 'items.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    lint(items, lang, cfg)
    img, th = load_images(root, items)
    audio_files, cps = attach_audio(root, items, args.max_level)

    fonts = {**lang.get('fonts', {}), **cfg.get('fonts', {})}
    css = {**lang.get('css', {}), '--nl': str(nl)}
    page_title = cfg.get('page_title') or cfg['title']
    locale = cfg.get('locale') or {'zh': 'zh-CN', 'en': 'en-US'}.get(code.split('-')[0], code)
    data = {
        'items': items, 'sites': sites, 'img': img, 'th': th, 'ui': ui, 'levels': levels,
        'lang': {k: lang[k] for k in ('display', 'split', 'sentence_end', 'ordinal_sep', 'ordinals', 'norm', 'voice')},
        'title': cfg['title'], 'page_title': page_title, 'eyebrow': cfg.get('eyebrow', ''), 'lede': cfg.get('lede', ''),
        'pigments': cfg.get('pigments', []), 'cps': cps or lang['cps'], 'locale': locale,
        'key': cfg.get('storage_key') or cfg.get('id') or 'audioguide',
    }
    extra = {
        'html_lang': cfg.get('html_lang') or lang['html_lang'], 'page_title': page_title,
        'font_google': fonts.get('google', ''), 'font_serif': fonts.get('serif', 'serif'), 'font_italic': fonts.get('italic', 'serif'),
        'css_vars': ';'.join('%s:%s' % kv for kv in css.items()) + ';', 'extra_css': cfg.get('extra_css', ''),
    }
    tpl = open(TEMPLATE, encoding='utf-8').read()
    page = render(tpl, data, ui, extra)

    plain = json.loads(json.dumps(data))
    for it in plain['items']:
        it.pop('aud', None)
    open(os.path.join(root, 'standalone.html'), 'w', encoding='utf-8').write(render(tpl, plain, ui, extra))

    dist = os.path.join(root, 'dist')
    shutil.rmtree(dist, ignore_errors=True)
    os.makedirs(os.path.join(dist, 'a'))
    open(os.path.join(dist, 'index.html'), 'w', encoding='utf-8').write(page)
    total = len(page.encode('utf-8'))
    for f in audio_files:
        shutil.copy(os.path.join(root, 'audio', f), os.path.join(dist, f))
        total += os.path.getsize(os.path.join(root, 'audio', f))

    print('language %s | levels %s | %d items in %d sites | %d images | %d recordings%s'
          % (code, ', '.join(l['name'] for l in levels), len(items), len(sites), len(img), len(audio_files),
             ' | measured speed %.1f chars/s' % cps if cps else ' | (no recordings: reading-time labels use the language default)'))
    print('dist/: %.1f MiB (index.html %.1f MiB)' % (total / 1048576, len(page.encode('utf-8')) / 1048576))
    for s in sites:
        print('  %-14s %3d stops  %s' % (s['id'], len(s['ids']), ' | '.join(g['name'] or '(no groups)' for g in s['groups'])[:110]))
    if WARN:
        print('\n%d warning(s):' % len(WARN))
        for w in WARN:
            print('  - ' + w)


if __name__ == '__main__':
    main()
