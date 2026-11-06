# Voices and recording

## Engines

`voice.engine` in `guide.json` (or `--engine`):

| Engine | Quality | Cost and privacy | Needs |
|---|---|---|---|
| `edge` (default) | Natural neural voices, dozens of languages, several voices each | Free, no key. It is an unofficial online service used by Microsoft Edge's "read aloud": **the narration text is sent to Microsoft's servers**, there is no service-level promise, and it could change or disappear. Fine for a personal or non-commercial guide; for a commercial product use a licensed TTS via `command` | `pip install edge-tts`, internet, ffmpeg |
| `mac` | Compact system voices; robotic. Premium or Enhanced voices (System Settings, Accessibility, Spoken Content, System Voice, Manage Voices) are better | Offline, nothing leaves the machine | macOS `say`, ffmpeg |
| `command` | Whatever you plug in | The user's own account or model | A shell command that writes an audio file |
| none | The phone's own voice reads the text on the page; quality depends on the phone | Nothing recorded; the guide is tiny | Set no recordings (skip `gen_audio.py`) |

`command` example: `"voice": {"engine": "command", "name": "my-voice", "command": ["python3", "tts.py", "{text_file}", "{out}"]}`. The script reads the text file and writes any audio file ffmpeg can read to `{out}` (wav, mp3, ogg). `{voice}` and `{rate}` are also substituted. Use credentials the user gave you for this purpose; do not borrow whatever cloud login happens to exist on the machine.

## Picking a voice

- Language first: `list_voices.py --locale <lang>` shows the actual Edge voices (gender, locale). Regional variants matter (`en-GB` vs `en-US`, `es-ES` vs `es-MX`, `zh-CN` vs `zh-TW`).
- Audition with `voice_samples.py` using the guide's own opening text. Offer at least one male and one female, and let the user listen. You cannot judge voice quality yourself.
- Pace: `voice.rate` for Edge is a percentage ("-8%", "+10%"); for `mac` it is words per minute. Listeners can also use the speed button on the page (0.8x to 1.5x), so a small adjustment is enough.
- Female/male neural voices differ little in cost. The one variable that matters is whether the user likes the sound over 40 minutes.

## What gets produced

- Each unit (heading, look-list item, sentence) is synthesised separately, trimmed of silence and joined with controlled pauses (heading 0.5 s, list item 0.45 s, sentence 0.2 s, paragraph end 0.5 s). That is how the page knows the start time of every sentence for highlighting.
- Encoded as mono 24 kHz MP3 at 40 kbps by default (`voice.bitrate`, e.g. `24k` for smaller). About 300 KB per minute: a 3.5-hour guide is about 65 MB. Phones fetch a track when the stop is played, so size matters on mobile data.
- File names include the voice tag: `a/<stop>-<level>-<voice>.mp3`.
- `audio/manifest.json` stores the voice name, pace and a hash of the text per track, so `gen_audio.py` re-records exactly the tracks whose voice, pace or text changed.

## Speed and parallelism

Edge synthesises about as fast as it can be asked: roughly 250 tracks (about 3.5 hours) in 25 minutes with 6 parallel requests. Raise `voice.jobs` cautiously; lower it if you see rate limiting. Run recording in the background; it writes the manifest after each track, so an interrupted run resumes where it stopped.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `edge-tts is not installed` | Use the virtualenv Python: `.venv/bin/python gen_audio.py ...`. `doctor.py` shows which Python has it |
| HTTP 429 / empty audio / timeouts | Rate limit or network. The script retries six times with back-off. If tracks still fail, `JOBS=3` (or `--jobs 3`) and re-run; finished tracks are skipped |
| `libmp3lame` missing | Install an ffmpeg build with it (`brew install ffmpeg`) |
| Highlight drifts from the audio | The text was edited after recording or the unit counts differ. Run `check_units.py`; re-run `gen_audio.py` (it detects changed text) |
| Voice says a word wrongly (a name, a numeral) | Add a `norm` rule in the project's `lang` block, or respell it in the text ("Leo the Tenth"), then re-record that stop with `--ids` |
| A track sounds cut or has a long pause | Very long sentences or odd punctuation. Shorten the sentence; re-record that stop |
| Phone plays the device voice instead of the recording | The mp3 failed to load (wrong path, host blocks the file type, upload incomplete). The status line on the page shows "recorded" when the mp3 is playing |
| Changed voice but a phone still plays the old one | Same file name reused. The scripts avoid this by naming files with the voice; do not rename them back |

## Re-voicing an existing guide

1. Set the new `voice.name` (after an audition) in `guide.json`.
2. `gen_audio.py` (records every track, because the voice differs), `build.py`, `check_units.py`.
3. `gen_audio.py --prune` moves the old voice's mp3s into `audio/archive/` (nothing is deleted).
4. Republish (`publishing.md`): the old files must be deleted from the host as well.
