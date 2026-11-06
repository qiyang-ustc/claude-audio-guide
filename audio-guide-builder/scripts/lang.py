"""Language handling shared by build.py, gen_audio.py and check_units.py.

Everything language-specific lives in JSON (assets/lang/<code>.json, optionally overridden by the
project's guide.json "lang" block), so adding a language never needs a code change:

  split      how a paragraph becomes sentences (sentences are the playback / highlight units)
  norm       ordered regex rules turning written text into text a TTS voice reads well
  ordinals   spoken "First, ..." prefixes for the look-list
  sentence_end / ordinal_sep   punctuation the TTS text is assembled with
  cps        fallback reading speed (characters per second) for the "about N min" labels

The same `norm` rules are shipped to the page (D.lang.norm) so the browser-voice fallback reads the
text exactly like the recorded voice does. Rules therefore use only regex features that Python's `re`
and JavaScript share, and replacements use $1-style groups.
"""
import json, os, re

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANG_DIR = os.path.join(SKILL_DIR, 'assets', 'lang')
UI_DIR = os.path.join(SKILL_DIR, 'assets', 'ui')

CJK_CODES = {'zh', 'ja', 'ko', 'yue'}


def _read(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load_lang(code, overrides=None):
    """assets/lang/<code>.json, falling back to the generic space-delimited or CJK template."""
    base_code = code.split('-')[0].lower()
    for c in (code, base_code):
        p = os.path.join(LANG_DIR, c + '.json')
        if os.path.exists(p):
            cfg = _read(p)
            break
    else:
        cfg = _read(os.path.join(LANG_DIR, '_cjk.json' if base_code in CJK_CODES else '_latin.json'))
        cfg['code'] = base_code
        cfg['display'] = cfg.get('display') if cfg.get('display') != 'generic' else base_code
        cfg['_generic'] = True
    return _merge(cfg, overrides)


def load_ui(code, project_dir=None, overrides=None):
    """English strings are the base, so a partial translation still renders. Order of precedence:
    project ui.<code>.json > shipped assets/ui/<code>.json > English; then guide.json "ui" overrides."""
    ui = _read(os.path.join(UI_DIR, 'en.json'))
    base_code = code.split('-')[0].lower()
    missing = []
    for c in dict.fromkeys([code, base_code]):
        cands = []
        if project_dir:
            cands.append(os.path.join(project_dir, 'ui.%s.json' % c))
        cands.append(os.path.join(UI_DIR, c + '.json'))
        found = next((p for p in cands if os.path.exists(p)), None)
        if found and c != 'en':
            tr = _read(found)
            missing = [k for k in ui if k not in tr and not k.startswith('_')]
            ui = _merge(ui, tr)
            break
    else:
        if base_code != 'en':
            missing = ['*']        # no translation at all; English UI will be shown
    return _merge(ui, overrides), missing


# ---------------------------------------------------------------- sentence splitting

def split_sentences(paragraph, lang):
    sp = lang['split']
    p = paragraph.strip()
    if not p:
        return []
    if sp['mode'] == 'cjk':
        t, c = re.escape(sp['terminators']), re.escape(sp.get('closers', ''))
        out = re.findall(r'[^%s\n]+[%s]+[%s]*|[^%s\n]+$' % (t, t, c, t), p)
        return [s.strip() for s in out if s.strip()]
    return _split_space(p, sp)


def _split_space(p, sp):
    """Split on . ! ? followed by whitespace and a capital, digit or opening quote.

    The failure mode is deliberately "don't split": an abbreviation such as "St." or "c. 1485", an
    initial ("J. M. W. Turner") or a decimal never ends a unit. Two sentences merged into one unit only
    costs a coarser highlight; a sentence cut in half sounds broken."""
    abbr = {a.lower().rstrip('.') for a in sp.get('abbr', [])}
    term, close = re.escape(sp['terminators']), re.escape(sp.get('closers', ''))
    pat = re.compile('[%s]+[%s]*' % (term, close))
    opens = '"“‘\'([«¿¡'
    out, start, n = [], 0, len(p)
    for m in pat.finditer(p):
        e = m.end()
        if e < n and not p[e].isspace():
            continue
        rest = p[e:].lstrip()
        run = m.group(0).rstrip(sp.get('closers', '')) if sp.get('closers') else m.group(0)
        if rest:
            nxt = rest[0]
            if not (nxt.isupper() or nxt.isdigit() or nxt in opens):
                continue                      # lower-case continuation: not a sentence boundary
            if run == '.':
                toks = p[start:m.start()].split()
                last = toks[-1].strip(opens + ')]”’').lower() if toks else ''
                if last.rstrip('.') in abbr or re.fullmatch(r'[a-z]', last):
                    continue
        out.append(p[start:e].strip())
        start = e
    if p[start:].strip():
        out.append(p[start:].strip())
    return [s for s in out if s]


# ---------------------------------------------------------------- speech text

def _py_repl(repl):
    return re.sub(r'\$(\d)', r'\\g<\1>', repl)


def norm(text, lang):
    t = text
    for rule in lang.get('norm', []):
        flags = re.I if 'i' in rule.get('flags', '') else 0
        t = re.sub(rule['re'], _py_repl(rule['to']), t, flags=flags)
    return t.strip() if lang['split']['mode'] != 'cjk' else t


def _ends_with_terminator(t, lang):
    return bool(t) and t[-1] in lang['split']['terminators'] + lang['split'].get('closers', '')


def units_for(item, level, lang):
    """(text for the TTS voice, pause in seconds) per playback unit, in page order.
    The unit count and order must equal what the page builds in renderNarr()."""
    end, sep, ords = lang['sentence_end'], lang['ordinal_sep'], lang['ordinals']
    out = []
    for sec in item['sections']:
        if sec['lv'] != level:
            continue
        h = norm(sec['h'], lang)
        out.append((h if _ends_with_terminator(h, lang) else h + end, 0.5))
        if 'list' in sec:
            for k, t in enumerate(sec['list']):
                body = norm(t, lang)
                prefix = (ords[k] if k < len(ords) else str(k + 1)) + sep
                out.append((prefix + body + ('' if _ends_with_terminator(body, lang) else end), 0.45))
        else:
            for para in sec['paras']:
                for j, t in enumerate(para):
                    out.append((norm(t, lang), 0.5 if j == len(para) - 1 else 0.2))
    return out


def unit_count(item, level):
    """Number of playback units the page shows for one level of an item (independent of language)."""
    n = 0
    for sec in item['sections']:
        if sec['lv'] == level:
            n += 1 + (len(sec['list']) if 'list' in sec else sum(len(p) for p in sec['paras']))
    return n


def voice_tag(voice):
    """Short, filename-safe tag for a voice, e.g. zh-CN-XiaoxiaoNeural -> xiaoxiao."""
    name = voice.split('-')[-1] if '-' in voice else voice
    name = re.sub(r'Neural$', '', name)
    return re.sub(r'[^a-z0-9]+', '', name.lower()) or 'voice'
