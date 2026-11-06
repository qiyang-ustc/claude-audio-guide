# Publishing

Nothing is published unless the user asks. Before you do anything public, say in one sentence what becomes visible to whom and wait for a clear yes; permission for one publish does not carry to the next.

## What you publish

`dist/` after a clean build: `index.html` (the whole page, images inline, usually 0.1-5 MB) and `a/*.mp3`. All paths are relative, so it works at a domain root or in a sub-folder. Nothing needs a server beyond serving static files with correct types (`audio/mpeg` for mp3). `standalone.html` is a single-file alternative with device voice only, good for sending by chat or email.

## Options

| Option | How | Notes |
|---|---|---|
| Local only | open `dist/index.html` through `python3 -m http.server --directory dist` | Audio is fetched with `fetch()`, which browsers block on `file://`; use a local server for the full experience |
| Zip to share | `cd dist && zip -r ../guide.zip .` | Recipients unzip and serve, or open `standalone.html` for the voice-less version |
| Static host (GitHub Pages, Netlify, Cloudflare Pages, S3, any web server) | upload `dist/` as is | The user's account; ask for the target, do not invent one. Free tiers are fine for tens of megabytes |
| Claude artifact link | the Artifact tool, below | The link is readable by anyone who has it (organisation settings can restrict that) |

## The Artifact tool in detail

If you have an Artifact tool, a guide can be published to a shareable link. Learn its limits before the first call:

- One publish accepts at most **255 `files` entries (deletions count) and about 64 MB**; one version holds at most **511 files**; the page itself must be 16 MB or less. A 250-track guide therefore needs two or three publishes.
- `python3 $SKILL_DIR/scripts/publish_batches.py --dist dist [--live-listing live.txt]` plans the batches. Give it the live file list when updating, and it uploads only new or changed files and schedules deletions of stale ones, interleaved so the version never exceeds the file limit. Each `batch-N.json` is a `{path: path | null}` map: pass it as `files`, with `root` set to the absolute `dist/` path and `file_path` set to `dist/index.html`. `null` deletes a published file.
- Publish the batches back to back. The first publish already carries the new `index.html`, so recordings not yet uploaded fall back to the phone's voice until the last batch lands.
- First publish: pass `icon` and a stable page title (the HTML `<title>`). Redeploys: pass the artifact `url`, omit `icon`, keep the title, and pass the same `file_path`.
- The tool may refuse an update to an artifact this conversation has not viewed. Read the live version (the Artifact tool's `read` action), check that nothing but your own content differs, then publish again. A refusal that says it was identical is solved by reading the saved live source.
- Keep each publish's `label` meaningful ("Spanish voice 2/3").

## Verify after publishing

1. List the live files (the tool's `list` with scope `files`) and compare the count and a few byte sizes with `dist/` (the live `index.html` is a few hundred bytes larger because the host wraps it).
2. Open the live page in a browser tool, open a stop, press play and confirm the status line says the recording is playing (not the device voice) and the highlight advances. Do this for a track from each batch.
3. If you cannot open it (no browser tool), say the live check was not done.
4. Record the URL, date, version and what changed in `NOTES.md`.

## Updating later

- New or edited stops: write, `build.py`, `gen_audio.py` (records only what changed), `build.py`, `check_units.py`, then publish the changed files plus `index.html`.
- New voice: all tracks change name; plan batches with the live listing so the old ones are deleted.
- Removing a published guide: only on the user's request; deleting the artifact breaks everyone's link.

## Privacy and rights, in one line each

- The page carries the AI-disclosure footer; keep it.
- Images are public domain or the user's own; the guide contains no copied label text.
- The Edge voice sent the text to Microsoft during recording; once recorded, visitors never contact it.
- The page loads Google Fonts from `fonts.googleapis.com` for typography (set `fonts.google` to `""` and system fonts for a no-third-party page).
