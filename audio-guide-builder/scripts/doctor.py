#!/usr/bin/env python3
"""Check that this machine can build and record a guide, and say exactly how to fix what is missing.

  doctor.py [--net]      --net also does a one-sentence test synthesis with Edge TTS (needs internet)

Run it with the same python you will use for gen_audio.py. Nothing is installed automatically.
"""
import argparse, asyncio, importlib.util, os, platform, shutil, subprocess, sys, tempfile


def row(ok, name, detail, fix=''):
    print('%s %-22s %s' % ('ok  ' if ok else 'MISSING' if fix else 'note', name, detail))
    if not ok and fix:
        print('      fix: ' + fix)
    return ok or not fix


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--net', action='store_true')
    a = ap.parse_args()
    good = True
    py = sys.version_info
    good &= row(py >= (3, 9), 'python', '%d.%d.%d at %s' % (py[0], py[1], py[2], sys.executable), 'install Python 3.9 or newer')
    ff = shutil.which('ffmpeg')
    has_mp3 = False
    if ff:
        enc = subprocess.run([ff, '-hide_banner', '-encoders'], capture_output=True, text=True).stdout
        has_mp3 = 'libmp3lame' in enc
    good &= row(bool(ff) and has_mp3, 'ffmpeg + libmp3lame', ff or 'not found',
                'macOS: brew install ffmpeg   Debian/Ubuntu: sudo apt install ffmpeg   (it must include libmp3lame)')
    have_edge = importlib.util.find_spec('edge_tts') is not None
    row(have_edge, 'edge-tts (voice)', 'importable' if have_edge else 'not installed',
        'python3 -m venv .venv && .venv/bin/pip install edge-tts pillow   (then run scripts with .venv/bin/python)')
    have_pil = importlib.util.find_spec('PIL') is not None
    row(have_pil, 'Pillow (images)', 'importable' if have_pil else 'not installed (only needed when the guide has images)',
        'pip install pillow')
    if platform.system() == 'Darwin':
        row(bool(shutil.which('say')), 'macOS say', 'available: offline engine "mac"' if shutil.which('say') else 'not found')
    if a.net:
        if not have_edge:
            print('skip net test: edge-tts missing')
        else:
            import edge_tts

            async def t():
                with tempfile.TemporaryDirectory() as td:
                    p = os.path.join(td, 't.mp3')
                    await edge_tts.Communicate('This is a test.', 'en-US-AriaNeural').save(p)
                    return os.path.getsize(p)
            try:
                n = asyncio.run(t())
                row(n > 0, 'edge-tts network', 'synthesised %d bytes' % n, 'check the internet connection / proxy')
            except Exception as e:  # noqa: BLE001
                good = row(False, 'edge-tts network', repr(e)[:120], 'check the internet connection; the service is unofficial and can change') and good
    print('\nready to record with Edge voices' if (good and have_edge) else '\nbuild works; recording needs the items marked MISSING (or use another engine)' if good else '\nfix the MISSING items above first')
    sys.exit(0 if good else 1)


if __name__ == '__main__':
    main()
