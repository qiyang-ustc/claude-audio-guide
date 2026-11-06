#!/usr/bin/env python3
"""Plan how to publish dist/ to a host that limits one upload (the Claude Artifact tool: at most 255 `files`
entries and about 64 MB per publish, and at most 511 files in a version).

  publish_batches.py --dist DIR [--live-listing FILE] [--out DIR] [--max-entries 250] [--max-mb 55] [--limit 500]

--live-listing  text of the live file list (the Artifact "list files" output, or one path per line). With it,
                only new/changed files are uploaded and stale files are scheduled for deletion; without it,
                every file in dist/ is treated as new.
Writes <out>/batch-1.json, batch-2.json, ... each a {"published/path": "published/path" | null} map: pass it as
the `files` argument (with root = dist and file_path = dist/index.html) in order. null deletes a live file.
Removals are interleaved with additions so the version never holds more than --limit files.

Order matters for visitors: the first publish already replaces index.html, so recordings not yet uploaded fall back
to the device voice until the last batch lands. Publish the batches back to back.
"""
import argparse, json, os, re, sys


def walk(dist):
    out = {}
    for base, _, names in os.walk(dist):
        for n in names:
            p = os.path.join(base, n)
            out[os.path.relpath(p, dist).replace(os.sep, '/')] = os.path.getsize(p)
    return out


def parse_listing(path):
    live = {}
    for line in open(path, encoding='utf-8'):
        m = re.search(r'"([^"]+)"\s+\S+\s+(\d+) bytes', line)
        if m:
            live[m.group(1)] = int(m.group(2))
        elif line.strip() and not line.startswith(('Published', '[')):
            live[line.strip().lstrip('- ').strip('"')] = -1
    return live


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dist', default='dist')
    ap.add_argument('--live-listing')
    ap.add_argument('--out', default='publish-batches')
    ap.add_argument('--max-entries', type=int, default=250)
    ap.add_argument('--max-mb', type=float, default=55)
    ap.add_argument('--limit', type=int, default=500)
    a = ap.parse_args()
    local = walk(a.dist)
    local.pop('index.html', None)                      # index.html travels as file_path in every publish
    live = parse_listing(a.live_listing) if a.live_listing else {}
    live.pop('index.html', None)
    adds = [(p, s) for p, s in sorted(local.items()) if live.get(p) != s]
    removes = sorted(p for p in live if p not in local)
    cur = len(live)
    maxb = int(a.max_mb * 1048576)
    os.makedirs(a.out, exist_ok=True)
    batches = []
    while adds or removes:
        entries, size, n_new, n_rm = {}, 0, 0, 0
        while adds and len(entries) < a.max_entries:
            p, s = adds[0]
            if entries and size + s > maxb:
                break
            grows = p not in live
            if grows and cur + n_new + 1 - n_rm > a.limit:
                if removes and len(entries) + 2 <= a.max_entries:
                    entries[removes.pop(0)] = None
                    n_rm += 1
                else:
                    break
            adds.pop(0)
            entries[p] = p
            size += s
            n_new += 1 if grows else 0
        while removes and len(entries) < a.max_entries:
            entries[removes.pop(0)] = None
            n_rm += 1
        if not entries:
            sys.exit('cannot make progress: a single file exceeds the size limit, or --limit is too low')
        cur += n_new - n_rm
        for p, v in entries.items():
            if v is None:
                live.pop(p, None)
            else:
                live[p] = 0
        batches.append((entries, size, n_new, n_rm, cur))
    if not batches:
        print('nothing to upload: dist/ matches the live listing (publish index.html alone if it changed)')
        return
    for i, (entries, size, n_new, n_rm, after) in enumerate(batches, 1):
        path = os.path.join(a.out, 'batch-%d.json' % i)
        json.dump(entries, open(path, 'w'), ensure_ascii=False, indent=0)
        print('batch %d: %3d entries (%d uploads, %d deletions), %.1f MB, live files afterwards: %d  -> %s'
              % (i, len(entries), n_new, n_rm, size / 1048576, after + 1, path))
    print('(+1 for index.html in every publish.) Publish in order, then list the live files and compare with dist/.')


if __name__ == '__main__':
    main()
