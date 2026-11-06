#!/usr/bin/env python3
"""Record the narration: one mp3 per item x level, plus the time of every sentence for highlighting.

  gen_audio.py [--project DIR] [--ids a,b] [--levels 1,2] [--engine edge|mac|command]
               [--voice NAME] [--rate +0%] [--jobs N] [--force] [--dry-run] [--prune]

Run build.py first (it writes items.json). Settings default to guide.json "voice":
  {"engine": "edge", "name": "en-US-AriaNeural", "rate": "+0%"}
Engines
  edge     Microsoft Edge neural voices via the `edge-tts` package. Free, no key, many languages. It is an
           unofficial online service: the narration text is sent to Microsoft's servers.
  mac      macOS `say` (offline). Fine for a draft; compact voices sound robotic.
  command  any TTS you can call from a shell, e.g. {"engine": "command", "name": "mytts",
           "command": ["mytts", "--in", "{text_file}", "--out", "{out}"]}. It must write an audio file
           ffmpeg can read to {out}. Use this to plug in a cloud voice the user has credentials for.

Output (same for every engine)
  audio/a/<id>-<level>-<voicetag>.mp3   the voice is part of the file name, because phones cache mp3s by
                                        URL: a new voice under an old name would play the old recording
  audio/manifest.json   {id: {level: {f, t: [sentence start seconds], d: seconds, v: voice, r: rate, h: text hash}}}
A track is skipped when its voice, rate and text hash are unchanged, so re-running only records what changed.

Needs ffmpeg with libmp3lame on PATH.
"""
import argparse, array, asyncio, hashlib, json, os, random, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402

SR = 24000


# ------------------------------------------------------------------ engines (async: text -> audio file)

class Engine:
    def __init__(self, kind, voice, rate, command, sem):
        self.kind, self.voice, self.rate, self.command, self.sem = kind, voice, rate, command, sem
        if kind == 'edge':
            try:
                import edge_tts  # noqa: F401
            except ImportError:
                sys.exit('edge-tts is not installed. In a virtualenv: pip install edge-tts   (see scripts/doctor.py)')
        elif kind == 'mac' and not shutil.which('say'):
            sys.exit('engine "mac" needs macOS `say`')
        elif kind == 'command' and not command:
            sys.exit('engine "command" needs guide.json voice.command (a list with {text_file} and {out})')

    async def synth(self, text, path):
        async with self.sem:
            last = None
            for attempt in range(6):
                try:
                    await self._once(text, path)
                    if os.path.exists(path) and os.path.getsize(path) > 0:
                        return
                    last = 'empty output'
                except Exception as e:  # network blips, rate limits: back off and retry
                    last = repr(e)
                await asyncio.sleep(1.5 * (attempt + 1) + random.random())
            raise RuntimeError('%s failed for %r: %s' % (self.kind, text[:40], last))

    async def _once(self, text, path):
        if self.kind == 'edge':
            import edge_tts
            await edge_tts.Communicate(text, self.voice, rate=self.rate or '+0%').save(path)
        elif self.kind == 'mac':
            cmd = ['say', '-v', self.voice, '-o', path, '--file-format=WAVE', '--data-format=LEI16@%d' % SR]
            if self.rate and self.rate.isdigit():
                cmd += ['-r', self.rate]
            await asyncio.to_thread(subprocess.run, cmd + ['--', text], check=True, capture_output=True)
        else:
            txt = path + '.txt'
            open(txt, 'w', encoding='utf-8').write(text)
            cmd = [c.replace('{text_file}', txt).replace('{out}', path).replace('{voice}', self.voice or '').replace('{rate}', self.rate or '')
                   for c in self.command]
            await asyncio.to_thread(subprocess.run, cmd, check=True, capture_output=True)


# ------------------------------------------------------------------ audio plumbing

def decode(path):
    p = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-f', 's16le', '-ar', str(SR), '-ac', '1', '-'], capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode()[:300])
    pcm = array.array('h')
    pcm.frombytes(p.stdout)
    return pcm


def trim(pcm, thr=300, keep=int(SR * 0.04)):
    """Cut leading/trailing silence so the pauses between sentences are the ones we choose."""
    n = len(pcm)
    a = 0
    while a < n and abs(pcm[a]) < thr:
        a += 1
    b = n
    while b > a and abs(pcm[b - 1]) < thr:
        b -= 1
    return pcm[max(0, a - keep):min(n, b + keep)]


def encode(pcm, out_path, bitrate):
    p = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                        '-b:a', bitrate, '-codec:a', 'libmp3lame', out_path], input=pcm.tobytes(), capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode()[:300])


async def render_units(engine, units):
    """-> (pcm, start second of each unit)"""
    with tempfile.TemporaryDirectory() as td:
        paths = {}
        tasks = []
        for k, (text, _pause) in enumerate(units):
            if any(ch.isalnum() for ch in text):
                paths[k] = '%s/u%d.audio' % (td, k)
                tasks.append(engine.synth(text, paths[k]))
        await asyncio.gather(*tasks)
        pcm, starts = array.array('h'), []
        for k, (text, pause) in enumerate(units):
            starts.append(round(len(pcm) / SR, 2))
            if k in paths:
                pcm.extend(trim(await asyncio.to_thread(decode, paths[k])))
            pcm.extend(array.array('h', [0]) * int(SR * pause))
    pcm.extend(array.array('h', [0]) * int(SR * 0.3))
    return pcm, starts


def text_hash(units):
    return hashlib.sha1('\n'.join(t for t, _ in units).encode('utf-8')).hexdigest()[:12]


# ------------------------------------------------------------------ main

async def run(args):
    root = os.path.abspath(args.project)
    cfg = json.load(open(os.path.join(root, 'guide.json'), encoding='utf-8'))
    lang = L.load_lang(cfg['language'], cfg.get('lang'))
    vcfg = cfg.get('voice', {})
    kind = args.engine or vcfg.get('engine', 'edge')
    voice = args.voice or vcfg.get('name') or (lang.get('edge_voices') or [{}])[0].get('name')
    if not voice and kind != 'command':
        sys.exit('no voice chosen: set guide.json voice.name or pass --voice (python3 list_voices.py --locale xx)')
    rate = args.rate if args.rate is not None else vcfg.get('rate', '+0%' if kind == 'edge' else '')
    tag = L.voice_tag(voice or 'custom')
    bitrate = vcfg.get('bitrate', '40k')
    items_path = os.path.join(root, 'items.json')
    if not os.path.exists(items_path):
        sys.exit('items.json missing: run build.py first')
    items = json.load(open(items_path, encoding='utf-8'))
    out = os.path.join(root, 'audio')
    os.makedirs(os.path.join(out, 'a'), exist_ok=True)
    manp = os.path.join(out, 'manifest.json')
    man = json.load(open(manp)) if os.path.exists(manp) else {}
    only = set(args.ids.split(',')) if args.ids else None
    levels = [int(x) for x in args.levels.split(',')] if args.levels else [1, 2, 3]

    jobs = []
    for lvl in levels:
        for it in items:
            if only and it['id'] not in only:
                continue
            units = L.units_for(it, lvl, lang)
            if not units:
                continue
            e = man.get(it['id'], {}).get(str(lvl))
            if (not args.force and e and e.get('v') == voice and e.get('r', '') == (rate or '') and e.get('h') == text_hash(units)
                    and os.path.exists(os.path.join(out, e['f']))):
                continue
            jobs.append((it, lvl, units))
    chars = sum(len(t) for _, _, us in jobs for t, _ in us)
    print('engine %s | voice %s | rate %s | %d tracks to record (%d characters)' % (kind, voice, rate or 'default', len(jobs), chars), flush=True)
    if args.dry_run or not jobs:
        if args.prune:
            prune(out, man)
        return
    sem = asyncio.Semaphore(args.jobs or int(vcfg.get('jobs', 6)))
    engine = Engine(kind, voice, rate, vcfg.get('command'), sem)

    async def job(it, lvl, units):
        pcm, starts = await render_units(engine, units)
        f = 'a/%s-%d-%s.mp3' % (it['id'], lvl, tag)
        await asyncio.to_thread(encode, pcm, os.path.join(out, f), bitrate)
        return it['id'], lvl, {'f': f, 't': starts, 'd': round(len(pcm) / SR, 2), 'v': voice, 'r': rate or '', 'h': text_hash(units)}

    done = 0
    for fut in asyncio.as_completed([asyncio.ensure_future(job(*j)) for j in jobs]):
        iid, lvl, res = await fut
        man.setdefault(iid, {})[str(lvl)] = res
        done += 1
        json.dump(man, open(manp, 'w'), ensure_ascii=False)
        print('%d/%d %s L%d %.0fs' % (done, len(jobs), iid, lvl, res['d']), flush=True)
    print('finished %d of %d' % (done, len(jobs)), flush=True)
    if args.prune:
        prune(out, man)


def prune(out, man):
    """Move recordings no manifest entry points at into audio/archive/ (nothing is deleted)."""
    used = {v['f'].split('/')[-1] for a in man.values() for v in a.values()}
    adir = os.path.join(out, 'a')
    stale = [f for f in os.listdir(adir) if f.endswith('.mp3') and f not in used]
    if stale:
        os.makedirs(os.path.join(out, 'archive'), exist_ok=True)
    for f in stale:
        shutil.move(os.path.join(adir, f), os.path.join(out, 'archive', f))
    print('pruned: moved %d unreferenced recordings to audio/archive/' % len(stale))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project', default='.')
    ap.add_argument('--ids')
    ap.add_argument('--levels')
    ap.add_argument('--engine', choices=['edge', 'mac', 'command'])
    ap.add_argument('--voice')
    ap.add_argument('--rate')
    ap.add_argument('--jobs', type=int)
    ap.add_argument('--force', action='store_true', help='re-record even if unchanged')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--prune', action='store_true', help='move unreferenced old recordings to audio/archive/')
    asyncio.run(run(ap.parse_args()))


if __name__ == '__main__':
    main()
