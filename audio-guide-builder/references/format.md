# Project format

A project is a folder:

```
guide.json            all configuration (what the interview produces)
content/*.md          the narration, one block per stop; files are read in name order
img/<name>.jpg        optional pictures (also .jpeg, .png), referenced from content
ui.<code>.json        optional interface translation for a language the skill does not ship
audio/                recordings and manifest.json (written by gen_audio.py)
items.json            parsed content (written by build.py; the recorder reads it)
standalone.html       the guide in one file, device voice only (written by build.py)
dist/                 what you publish: index.html and a/*.mp3 (rewritten by every build)
samples/              voice auditions
NOTES.md              hand-over notes
```

`items.json`, `standalone.html`, `dist/` and `audio/manifest.json` are generated; do not hand-edit them.

## guide.json

| Key | Required | Meaning |
|---|---|---|
| `title` | yes | Big heading on the home page and the label in the lock-screen player |
| `language` | yes | Narration language code (`en`, `zh`, `es`, `fr`, `de`, `it`, `ja`, ...). Picks `assets/lang/<code>.json` (a generic template if absent) |
| `sites` | yes | List of places (below). Each stop belongs to one site |
| `page_title` | no | Browser tab title; default `title` |
| `eyebrow` | no | Small italic line above the title (a place name in the local language works well) |
| `lede` | no | One or two sentences under the title |
| `ui_language` | no | Language of buttons and labels; default `language` |
| `levels` | no | 1-3 entries `{"name": "Quick", "sub": "The essentials"}`; default from the UI file. Stops may use levels 1..N |
| `voice` | no | `{"engine": "edge", "name": "en-US-AriaNeural", "rate": "+0%", "bitrate": "40k", "jobs": 6}`; `engine` is `edge`, `mac` or `command` (then `command`: argv list with `{text_file}` and `{out}`) |
| `locale` | no | BCP-47 tag used when the phone's own voice is the fallback; default derived from `language` |
| `html_lang` | no | `<html lang>`; default from the language file |
| `lang` | no | Overrides merged into the language file (abbreviations, ordinals, `norm` rules, fonts, css). See `languages.md` |
| `ui` | no | Overrides for individual interface strings |
| `fonts` | no | `{"google": "family=...&display=swap", "serif": "CSS font stack", "italic": "..."}`; defaults from the language file |
| `extra_css` | no | Raw CSS appended last, e.g. `:root{--vermilion:#0B6E4F}` to recolour the accent |
| `pigments` | no | Up to five labels for the decorative colour strip on the home page; leave out for no strip |
| `storage_key` / `id` | no | Prefix for the listener's saved settings in the browser; default `id`, else `audioguide` |

### Sites

The `//` comments below are for explanation only; guide.json itself must be plain JSON.

```json
{
  "id": "uffizi",                      // required; lower-case, no "s-" prefix; used in URLs
  "name": "Uffizi Gallery",            // required
  "native": "Galleria degli Uffizi",   // name in the local language, shown italic
  "kind": "Museum",                    // tag on the card
  "when": "Nov 7, 10:00-14:00",        // optional tag, handy for a trip itinerary
  "mark": "Uf",                        // letters on stops without a picture; default from the name
  "blurb": "...", "note": "...",       // card text; note appears on the site page
  "labels": ["Date","Medium","Size","Room"],   // names of the four detail fields (date, medium, size, room)
  "row_meta": ["artist","date"],       // which fields form the grey line under a stop in the list
  "foot": "...",                       // site-specific footer sentence (sources of room numbers etc.)
  "links": [{"t": "Official site", "u": "https://..."}],
  "auto_src": {"t": "Official collection", "u": "https://..."}   // appended to every stop's sources; a stop opts out with `nosrc: 1`
}
```

## content/*.md

```
@@ stop-id                         # lower-case letters, digits, hyphens; unique; not starting "s-"
site: uffizi                       # a site id; default is the first site
group: A. Early Renaissance · Rooms 1-8    # list heading; "numeral. Name · small right-hand note"
ord: 120                           # position in the site's order; default is file order * 10
title: The Birth of Venus          # required
orig: Nascita di Venere            # title in the original language (italic caption)
artist: Sandro Botticelli          # byline ("by:" also works)
date: c. 1485                      # detail fields; blank ones are hidden
medium: Tempera on canvas
size: 172.5 x 278.5 cm
room: Room 10-14                   # shown as a tag in the list
img: venus                         # img/venus.jpg
keywords: botticelli venus birth   # extra search words (alternative spellings, translations)
meta: custom grey line             # overrides row_meta; tag: overrides the list tag
look: First thing | Second thing | Third thing    # becomes a numbered list at the end of level 1
lookhead: Three things to notice   # optional heading for that list (default from the UI file)

## 1 | Heading of a level-1 section
Paragraph of sentences. Paragraphs are separated by a blank line.

Second paragraph.

## 2 | Heading of a level-2 section
...
@src Source title | https://example.org/page
@src Another source | https://example.org/other
```

Rules the build enforces or warns about:

- `## <level> | <heading>` with level 1..N (N = number of `levels`). Several sections per level are fine. Levels play cumulatively.
- Sentences are the highlight and tap-to-jump units. The splitter understands abbreviations, initials and decimals for spaced languages (it errs towards not splitting); use ordinary punctuation.
- Every item should have `@src` lines for pages actually read (warning otherwise unless the site has `auto_src`).
- Warnings for sentences over 260 characters (120 for CJK), skipped levels, placeholder text (TODO/TBD/lorem), missing images, recordings whose unit count no longer matches the text.
- A group's stops must be consecutive in the site's order; otherwise the build stops and names the group.
- Lines like `key: value` are only read between the `@@` line and the first `## `.

## Recordings

`audio/manifest.json`: `{ "<stop-id>": { "<level>": { "f": "a/<stop>-<level>-<voicetag>.mp3", "t": [start seconds of each unit], "d": seconds, "v": "<voice name>", "r": "<rate>", "h": "<text hash>" } } }`. A unit is a heading, a look-list item, or a sentence, in page order; the page highlights unit `k` when playback passes `t[k]`. Never edit by hand; `gen_audio.py` re-records any track whose voice, rate or hash differs, and `check_units.py` verifies consistency.
