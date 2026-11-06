#!/usr/bin/env python3
"""Make short audition clips so the user can choose a voice BEFORE the whole guide is recorded.

  voice_samples.py [--project DIR] [--voices v1,v2,v3] [--engine edge|mac|command] [--text "..."] [--out DIR]

Default text: the first few sentences of the project's own first stop (so the clip has the real names,
numbers and rhythm the guide will have). Default voices: the language file's suggested list.
Writes <project>/samples/<voicetag>.mp3 and prints the paths. Send them to the user and ask which one;
a robotic voice discovered after a full recording costs a full re-record.
"""
import argparse, asyncio, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
import gen_audio as G  # noqa: E402


async def main_async(args):
    root = os.path.abspath(args.project)
    cfg = json.load(open(os.path.join(root, 'guide.json'), encoding='utf-8'))
    lang = L.load_lang(cfg['language'], cfg.get('lang'))
    kind = args.engine or cfg.get('voice', {}).get('engine', 'edge')
    voices = args.voices.split(',') if args.voices else [v['name'] for v in lang.get('edge_voices', [])]
    if not voices:
        sys.exit('no voices to try: pass --voices (list them with list_voices.py --locale xx)')
    if args.text:
        units = [(args.text, 0.3)]
    else:
        items_path = os.path.join(root, 'items.json')
        if not os.path.exists(items_path):
            sys.exit('items.json missing: run build.py first, or pass --text')
        it = json.load(open(items_path, encoding='utf-8'))[0]
        lvl = 2 if any(s['lv'] == 2 for s in it['sections']) else 1
        units = L.units_for(it, lvl, lang)[:5]
    out_dir = args.out or os.path.join(root, 'samples')
    os.makedirs(out_dir, exist_ok=True)
    sem = asyncio.Semaphore(4)
    for v in voices:
        eng = G.Engine(kind, v, cfg.get('voice', {}).get('rate', '+0%' if kind == 'edge' else ''), cfg.get('voice', {}).get('command'), sem)
        pcm, _ = await G.render_units(eng, units)
        path = os.path.join(out_dir, '%s.mp3' % L.voice_tag(v))
        G.encode(pcm, path, '64k')
        print(v, '->', path, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project', default='.')
    ap.add_argument('--voices')
    ap.add_argument('--engine', choices=['edge', 'mac', 'command'])
    ap.add_argument('--text')
    ap.add_argument('--out')
    asyncio.run(main_async(ap.parse_args()))


if __name__ == '__main__':
    main()
