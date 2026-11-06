#!/usr/bin/env python3
"""Consistency check between the text, the recordings and dist/. Run after build.py + gen_audio.py.

  check_units.py [--project DIR] [--voice NAME]

Checks, per item and level that has text:
  - a recording exists, its file exists, and it was made with the expected voice
  - the number of sentence start times equals the number of units the page shows (otherwise the
    highlight drifts away from the audio)
  - the start times rise and stay inside the track; the file is not suspiciously small
  - the recording's text hash still matches the current text (catches edits made after recording)
and that dist/a holds exactly the recordings the manifest names. Exit status 1 if anything is wrong.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
from gen_audio import text_hash  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project', default='.')
    ap.add_argument('--voice', help='expected voice name (default: guide.json voice.name)')
    a = ap.parse_args()
    root = os.path.abspath(a.project)
    cfg = json.load(open(os.path.join(root, 'guide.json'), encoding='utf-8'))
    lang = L.load_lang(cfg['language'], cfg.get('lang'))
    voice = a.voice or cfg.get('voice', {}).get('name')
    items = json.load(open(os.path.join(root, 'items.json'), encoding='utf-8'))
    man = json.load(open(os.path.join(root, 'audio', 'manifest.json')))
    bad, missing, n, total, used = [], [], 0, 0.0, set()
    for it in items:
        for lvl in (1, 2, 3):
            if not any(s['lv'] == lvl for s in it['sections']):
                continue
            e = man.get(it['id'], {}).get(str(lvl))
            if not e or not os.path.exists(os.path.join(root, 'audio', e['f'])):
                missing.append((it['id'], lvl))
                continue
            n += 1
            total += e['d']
            used.add(e['f'].split('/')[-1])
            want = L.unit_count(it, lvl)
            if want != len(e['t']):
                bad.append((it['id'], lvl, 'units: text %d vs recording %d' % (want, len(e['t']))))
            if voice and e.get('v') != voice:
                bad.append((it['id'], lvl, 'voice %s, expected %s' % (e.get('v'), voice)))
            if e.get('h') and e['h'] != text_hash(L.units_for(it, lvl, lang)):
                bad.append((it['id'], lvl, 'text changed since recording'))
            t = e['t']
            if any(y < x for x, y in zip(t, t[1:])) or (t and t[-1] >= e['d']):
                bad.append((it['id'], lvl, 'start times not rising or beyond duration'))
            if os.path.getsize(os.path.join(root, 'audio', e['f'])) < 20000:
                bad.append((it['id'], lvl, 'suspiciously small file'))
    print('tracks checked: %d | total audio: %.1f min' % (n, total / 60))
    print('missing recordings:', missing or 'none')
    print('problems:', bad or 'none')
    ok = not missing and not bad
    dist = os.path.join(root, 'dist', 'a')
    if os.path.isdir(dist):
        have = set(os.listdir(dist))
        extra, lacking = sorted(have - used), sorted(used - have)
        print('dist/a: %d files | extra: %s | missing: %s' % (len(have), extra[:5] or 'none', lacking[:5] or 'none'))
        ok = ok and not extra and not lacking
    else:
        print('dist/a not built yet (run build.py)')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
