#!/usr/bin/env python3
"""List Edge neural voices for a locale or language, so the interview can offer real names.

  list_voices.py --locale en          # every English voice
  list_voices.py --locale es-MX       # one regional variant
  list_voices.py --engine mac --locale zh    # voices installed on this Mac (`say -v ?`)

Needs `pip install edge-tts` and network for the Edge list.
"""
import argparse, asyncio, subprocess, sys


async def edge(locale):
    try:
        import edge_tts
    except ImportError:
        sys.exit('edge-tts is not installed (pip install edge-tts, ideally in a virtualenv)')
    for v in sorted(await edge_tts.list_voices(), key=lambda v: (v['Locale'], v['Gender'], v['ShortName'])):
        if v['Locale'].lower().startswith(locale.lower()):
            tags = v.get('VoiceTag', {}).get('VoicePersonalities', [])
            print('%-28s %-7s %-7s %s' % (v['ShortName'], v['Gender'], v['Locale'], ', '.join(tags)))


def mac(locale):
    out = subprocess.run(['say', '-v', '?'], capture_output=True, text=True).stdout
    key = locale.replace('-', '_').lower()
    for line in out.splitlines():
        if key in line.lower().split('#')[0].replace('-', '_'):
            print(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--locale', required=True, help='language or locale prefix, e.g. en, fr, ja, zh-CN, es-MX')
    ap.add_argument('--engine', default='edge', choices=['edge', 'mac'])
    a = ap.parse_args()
    if a.engine == 'edge':
        asyncio.run(edge(a.locale))
    else:
        mac(a.locale)


if __name__ == '__main__':
    main()
