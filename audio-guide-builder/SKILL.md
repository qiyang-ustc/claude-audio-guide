---
name: audio-guide-builder
description: Build a mobile audio-guide web page for a museum, church, old town, walking route, garden, collection or any place, in any language. The result is a self-contained site with recorded neural-voice narration, three depth layers per stop (quick, standard, deep), tap-to-jump sentence highlighting and search. It interviews the user first (places, language, voice, depth, images, publishing), saves the answers to guide.json so anyone can reconfigure later, researches and writes sourced narration, records it, and can publish it. Use this whenever the user wants an audio guide, self-guided tour, museum companion, listenable travel guide, "narrate my trip notes", or wants to re-voice, translate, extend or republish a guide made this way, even if they never say "audio guide builder".
---

# Audio Guide Builder

Turns a subject ("the Uffizi", "the Alhambra gardens", "a food walk through Oaxaca") into a phone-friendly web guide: pick a stop or play the whole tour, choose how deep to go, follow the highlighted sentence while a pre-recorded voice reads it. The page is one HTML file plus mp3s, so it works on any static host, offline once loaded, and needs no account.

```
guide.json  +  content/*.md  +  img/*.jpg   --build.py-->   dist/index.html
                      |                                      dist/a/<stop>-<level>-<voice>.mp3
                      +--gen_audio.py (TTS)--> audio/manifest.json (sentence start times)
```

Two principles run through everything below. **The user configures by being asked, not by editing files**: every choice lives in `guide.json`, so a returning user (or someone else) can change language, voice or scope by answering questions. **The narration is factual writing under the user's name**: it has to be sourced, hedged where sources disagree, and honest about what was not checked.

`SKILL_DIR` below means the folder containing this file. Scripts are in `$SKILL_DIR/scripts`, run with `python3`; recording needs a Python that has `edge-tts` (see Step 0). Every script has `--help`.

## Step 0: Orient

1. Look for a `guide.json` in the working folder (or the folder the user names). If one exists, this is an **existing project**: read it, summarise the current setup in two or three lines, and ask what to change (voice, language, add or fix stops, republish). Jump to the matching step. If none, it is a **new project**: go to Step 1.
2. Run `python3 $SKILL_DIR/scripts/doctor.py`. It checks ffmpeg (with libmp3lame), `edge-tts`, Pillow and says how to fix each gap. Install packages into a virtualenv in the project (`python3 -m venv .venv && .venv/bin/pip install edge-tts pillow`) and tell the user you did; never install globally unasked. Then use `.venv/bin/python` for `gen_audio.py` and `voice_samples.py`.

## Step 1: Interview (this is how the guide gets configured)

Ask before researching or recording anything: a wrong language, a robotic voice or a 60-stop scope discovered late costs a full redo. Keep it short, because people answer five good questions and abandon twenty.

- Skip whatever the user already told you. Never re-ask.
- Use the AskUserQuestion tool when you have it: at most four questions per call, two to four options each, your recommendation first and marked "(Recommended)". Put open-ended topics (what and where) in plain chat first, since options cannot hold them. Without AskUserQuestion, ask the same things as a numbered list in plain text and accept "defaults" for the rest.
- Always offer an escape hatch: "use sensible defaults for everything else" is a valid answer, and then you pick from the Default column below and say what you picked.
- Match the user's language in the conversation, whatever language the guide will be in.

What to settle (full question bank with wording and options: `references/interview.md`):

| Topic | guide.json | Default | Why it matters |
|---|---|---|---|
| Subject and places (free text), visit date and time budget, who listens | `sites`, `lede` | none; always ask | Decides scope, order and the depth people will want |
| Narration language | `language` | the language the user writes in | Picks sentence splitting, number reading, fonts, voices |
| Page language | `ui_language` | same as narration | The buttons and labels; can differ (English page, Spanish narration) |
| Depth layers | `levels` | 3: Quick / Standard / Deep | Each stop is written once per layer; fewer layers means far less writing and recording |
| Coverage | content | highlights, about 10-15 stops | Recording time and the user's patience scale with it |
| Voice engine and voice | `voice` | Edge neural voice, chosen by audition | Voice quality is the thing users judge hardest (Step 5) |
| Images | `img:` per stop | none | Only public-domain images from Wikimedia Commons are used |
| Title, tone, look | `title`, `eyebrow`, `extra_css` | neutral warm-paper theme | Cosmetic; skip unless they care |
| Publishing | none | local files only | Publishing is a separate, explicit decision (Step 7) |

Then write `guide.json` (schema in `references/format.md`; start from `assets/examples/guide.en.json`), show a five-line summary of the choices, and get a go-ahead before the long steps. If the language is not `en` or `zh`, read `references/languages.md` now: it needs a small amount of setup (UI translation file, abbreviations).

Disclose two things the user would want to know before agreeing: the Edge engine sends the narration text to Microsoft's servers (an unofficial free service, no key), and the recordings are the machine's reading of AI-written text, so errors are possible and the page says so.

## Step 2: Plan the stops

Draft an outline (stop id, title, group, one line on why it earns a place) and show it before writing. For museums and sites with an official visitor map, take the stop order and room labels from that map and record its date; layouts change. Group stops so the list reads like the visit: groups appear as headings, and every group's stops must be consecutive (`ord:` values). Keep stop ids lower-case ASCII with hyphens; they become file names and URLs.

Ask the user to trim or add. Agreeing the list here is what keeps the writing step from going in circles.

## Step 3: Research and write

Read `references/content-guide.md` first: it holds the writing and sourcing standards, which are the part that makes the guide trustworthy. The essentials:

- One markdown block per stop in `content/*.md` (format: `references/format.md`), each layer a section: level 1 about a minute (the hook and what to look at), level 2 the backstory and technique, level 3 the debates and evidence. Playback is cumulative (depth 2 plays level 1 then level 2), so every layer must continue the story, not repeat the one before.
- Research from sources you actually read (official site, Wikipedia, museum and scholarly pages). List only URLs you opened as `@src` lines. Where the sources are silent, say so in the text ("the museum does not say"); where they disagree, say "accounts differ" and give both. Do not fill gaps from memory.
- Write for the ear: short sentences, no parenthetical asides, no tables, spell out numbers that a voice might misread, and keep opening hours and prices out of the narration (they go in the page footer and a link).
- For more than a handful of stops, split the research and drafting across subagents by group, then run a separate review pass in which a fresh agent checks every date, number, name and attribution against its listed sources and softens or deletes whatever is not supported.

Run `python3 $SKILL_DIR/scripts/build.py --project <dir>` as you go. It parses everything, warns about missing sources, over-long sentences, skipped levels and placeholder text, and writes `items.json`.

Images (only if the user wants them): `fetch_commons_image.py --search "..."` lists candidates with licence labels; download only those marked PD, then add `img: <name>` to the stop. It refuses anything else.

## Step 4: Check the words before spending time on voices

Have the user read one finished stop in `standalone.html` (device voice, no audio files) or in your own words. Catching a tone problem now costs seconds; after recording it costs the whole run.

## Step 5: Choose the voice by audition

Never record the whole guide with an unheard voice. List candidates for the language (`python3 $SKILL_DIR/scripts/list_voices.py --locale es`) or use the language file's suggestions, then:

```
.venv/bin/python $SKILL_DIR/scripts/voice_samples.py --project <dir> --voices <v1>,<v2>,<v3>
```

It reads the first stop's own opening so the clip has the real names and numbers. Send the clips to the user (SendUserFile when available, otherwise give the paths), let them listen, and ask which one. Offer male and female, and a slower or faster rate (`RATE=-8%`). Put the winner in `guide.json` `voice`. You cannot judge audio by ear, so say that plainly and let the user decide. Compact offline voices (macOS `say`) tend to sound robotic, and users reject them after a full recording has already been made; that is why this step exists.

Engines, rates, bring-your-own TTS and troubleshooting: `references/tts-and-voices.md`.

## Step 6: Build, record, verify

```
python3 $SKILL_DIR/scripts/build.py --project <dir>            # writes items.json
.venv/bin/python $SKILL_DIR/scripts/gen_audio.py --project <dir>   # records only what is new or changed
python3 $SKILL_DIR/scripts/build.py --project <dir>            # packs recordings into dist/
python3 $SKILL_DIR/scripts/check_units.py --project <dir>      # must exit 0
```

Recording takes roughly 25 minutes for 250 tracks; start it in the background and carry on, do not poll. Re-running is safe and cheap: a track is re-recorded only when its voice, pace or text changed (a text hash is stored). `--prune` moves recordings no stop uses into `audio/archive/`.

Then look at the real page, not just the checks. Serve `dist/` (`python3 -m http.server --directory dist`; restart it after every build, which recreates the folder) and open it in a browser tool if you have one: confirm the home list, a stop page, that pressing play shows the "recorded" status (not the device voice) and the highlight moves with the audio. Without a browser tool, say that this last check was not done.

## Step 7: Publish (only when asked, and confirm first)

Publishing makes the guide readable by anyone with the link, so ask what the user wants and say what it exposes: local files only (default), a zip of `dist/` to share, any static host the user already has, or a Claude artifact link. Details, including the upload limits that force batching and the exact procedure: `references/publishing.md`. After publishing, list what is live and compare it with `dist/`, then try the live page.

## Step 8: Hand over

Leave a short `NOTES.md` in the project: the interview answers, the chosen voice and why, which sources the stops rely on, what was not verified, how to re-record, and any publish record (URL, date, version). Tell the user how to change things later in one line each: "say 'switch to a male voice'" (re-record, republish), "say 'add a stop on X'" (write, record only the new track, republish), "say 'make a Spanish version'" (copy the project, translate; see `references/languages.md`).

## Gotchas collected the hard way

- **A new voice needs new file names.** The scripts put the voice in the file name (`a/stop-2-aria.mp3`) because phones cache mp3s by URL; reusing a name makes people hear the old voice. When republishing a changed voice, delete the old files from the host too.
- **The page and the recordings must come from the same text.** If you edit a stop after recording, re-run `gen_audio.py` (it detects the change) and `check_units.py`. A mismatch shifts the highlight away from the audio.
- **Keep the AI disclosure** on the page (`disclaimer` in the UI file). Narration is machine-written from public sources and is not an official guide; do not remove that to look more authoritative.
- **Do not over-trust room numbers, hours and prices.** They change; link the official source and say "check on site".
- **Images:** public-domain or CC0 only. A photo of an old statue is often still the photographer's copyright.
- **Copyright of sources:** paraphrase; quote at most a short phrase with attribution.
- **Never use credentials you were not given** for a cloud TTS or hosting account (for example an already-logged-in gcloud); ask for the project or key the user wants used.
- **Long recordings:** Edge may rate-limit (HTTP 429 or empty audio). The script backs off and retries; if it still fails, lower `JOBS` and re-run, finished tracks are skipped.

## Files in this skill

- `scripts/`: `build.py`, `gen_audio.py`, `voice_samples.py`, `list_voices.py`, `check_units.py`, `doctor.py`, `fetch_commons_image.py`, `publish_batches.py`, `lang.py` (shared)
- `assets/`: `template.html` (the page), `lang/` (per-language rules), `ui/` (interface strings), `examples/` (a runnable sample project)
- `references/`: `interview.md`, `format.md`, `content-guide.md`, `languages.md`, `tts-and-voices.md`, `publishing.md`

To try it end to end in a minute: copy `assets/examples/` to a new folder (`guide.en.json` becomes `guide.json`), run `build.py`, open `dist/index.html`.
