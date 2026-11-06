# claude-audio-guide

Use Claude Artifact as your free(?) audio guide.

A Claude skill, **audio-guide-builder**, that builds a phone-friendly audio guide for a museum, church, old town, walking route or any collection, in any language:

- a self-contained web page (one HTML file plus mp3s) with recorded neural-voice narration,
- three depth layers per stop (quick / standard / deep), sentence highlighting, tap to jump, search,
- configured by **answering questions** (places, language, voice, depth, images, publishing); the answers are saved in `guide.json`,
- sourced, hedged narration (it lists the pages it read and says "accounts differ" or "not verified" instead of guessing),
- optional publishing to a shareable Claude artifact link, a static host, or a zip.

## Install

Copy the skill folder into your Claude skills directory:

```bash
git clone https://github.com/qiyang-ustc/claude-audio-guide.git
cp -r claude-audio-guide/audio-guide-builder ~/.claude/skills/
```

Then ask Claude, for example: *"Make me an audio guide for the Uffizi for my trip on Saturday."* It will interview you first.

Requirements for recording: Python 3.9+, `ffmpeg` with libmp3lame, and `pip install edge-tts` (best in a virtualenv). `scripts/doctor.py` checks all of this.

## Try it without Claude

```bash
cd audio-guide-builder
mkdir /tmp/demo && cp assets/examples/guide.en.json /tmp/demo/guide.json && cp -r assets/examples/content /tmp/demo/
python3 scripts/build.py --project /tmp/demo
python3 -m http.server --directory /tmp/demo/dist      # then open http://localhost:8000
```

## Things to know

- The default voice engine (Edge neural voices via `edge-tts`) is an unofficial free service: **the narration text is sent to Microsoft's servers** while recording. Offline `say` (macOS) and bring-your-own TTS are supported too.
- The narration is written by AI from public sources and the page says so. Check facts that matter, and opening hours and tickets on the official site.
- Public-domain / CC0 images only (checked against Wikimedia Commons licence labels).
- Shipped languages: English and Chinese. Other languages work through a small config block and a UI translation that the skill creates with you; right-to-left languages are not supported yet.

## Status

Tested end to end in English with real recordings, and against a 87-stop Chinese guide. Not yet tested: other languages by native listeners, publishing through the Artifact tool from this skill's batch planner on a fresh guide, real phones. See `audio-guide-builder/evals/` for three test cases that have been written but not run.
