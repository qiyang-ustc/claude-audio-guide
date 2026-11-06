# Languages

Three things depend on the language, and each lives in a data file so no code changes are needed:

| What | Where | Ships with |
|---|---|---|
| Sentence splitting, number/abbreviation reading rules ("norm"), ordinals, reading speed, fonts, voice matching | `assets/lang/<code>.json`, merged with the project's `guide.json` `"lang"` block | `en`, `zh`; generic templates `_latin.json` (spaced scripts) and `_cjk.json` |
| Interface strings (buttons, labels, toasts, disclaimer) | `assets/ui/<code>.json`, or the project's `ui.<code>.json` | `en`, `zh`; anything missing falls back to English |
| The voice | `guide.json` `voice.name` (Edge voice names start with the locale, e.g. `fr-FR-DeniseNeural`) | suggestions per language in the language file |

`build.py` warns when a language has no shipped file or no UI translation; the page still builds, with English labels.

## Adding a language (about ten minutes)

1. **Voices.** `python3 $SKILL_DIR/scripts/list_voices.py --locale fr` shows real names. Pick 3-4 for the audition. Typical Edge names (verify with the script): `es-ES-ElviraNeural`, `es-MX-DaliaNeural`, `fr-FR-DeniseNeural`, `fr-FR-HenriNeural`, `de-DE-KatjaNeural`, `de-DE-ConradNeural`, `it-IT-ElsaNeural`, `it-IT-DiegoNeural`, `pt-BR-FranciscaNeural`, `ja-JP-NanamiNeural`, `ko-KR-SunHiNeural`.
2. **UI strings.** Copy `assets/ui/en.json` to `<project>/ui.<code>.json`, translate the values, keep every `{placeholder}` exactly, translate the `levels` names too. If the page language differs from the narration, set `ui_language`.
3. **Language block.** Add a `"lang"` object to `guide.json` that overrides the generic template. Fields that matter most:
   - `display` (the language's name in itself, shown in "no voice found" messages) and `html_lang`
   - `ordinals` spoken before look-list items ("Primero", "Segundo", ...) and `ordinal_sep` (": ")
   - `split.abbr`: abbreviations that end in a full stop but do not end a sentence (case-insensitive, without the dot)
   - `norm`: ordered regex rules from written text to speakable text. At least the word for "to" in number ranges, "c."/"ca." for circa, units. `$1`-style groups; keep to regex features shared by Python and JavaScript (no lookbehind).
   - `voice`: `lang_re` (regex on the phone's voice language tags, e.g. `^es`), `name_re`, `locales` (preferred tags)
   - `fonts` and `css` (`--lh` line height, `--h1-track`, `--caps`) when the default serif does not cover the script
   - `cps`: reading speed in characters per second, only until the first recording gives a measured value
4. **Check the splitting** by printing the sentences of one stop (`items.json` has them) and the speech text:
   `python3 -c "import sys;sys.path.insert(0,'$SKILL_DIR/scripts');import lang as L,json;l=L.load_lang('es',json.load(open('guide.json')).get('lang'));print(L.norm('c. 1485–1490, 96 × 110 cm',l))"`

Example block for Spanish (untested with native listeners; refine with the user):

```json
"lang": {
  "display": "español", "html_lang": "es",
  "ordinals": ["Primero", "Segundo", "Tercero", "Cuarto", "Quinto", "Sexto", "Séptimo", "Octavo"],
  "split": {"abbr": ["Sr", "Sra", "Srta", "Dr", "Dra", "Prof", "pág", "págs", "núm", "vol", "c", "ca", "cf", "S", "ss", "etc", "p.ej", "a.C", "d.C"]},
  "norm": [
    {"re": "(\\d)\\s*[–—]\\s*(\\d)", "to": "$1 a $2"},
    {"re": "\\s*[—–]\\s*", "to": ", "},
    {"re": "(\\d)\\s*[×x]\\s*(\\d)", "to": "$1 por $2"},
    {"re": "\\b(?:c|ca)\\.\\s*(?=\\d)", "to": "hacia "},
    {"re": "(\\d)\\s*cm\\b", "to": "$1 centímetros"},
    {"re": "[·•]", "to": " "},
    {"re": "\\s{2,}", "to": " "}
  ],
  "voice": {"lang_re": "^es", "locales": ["es-ES", "es-MX"], "name_re": "spanish|español"}
}
```

Objects merge key by key, so you only include what differs; lists (`split.abbr`, `norm`, `ordinals`) are replaced whole, so give the complete list you want.

## Making a second language version of an existing guide

Copy the project folder; never overwrite the original. In the copy: change `language` (and `ui_language`), `voice`, `title`/`lede`/site texts, delete `audio/` and `dist/` and `items.json`, translate every `content/*.md` keeping `@@ id`, `site`, `ord`, `img` and `@src` unchanged and translating `group`, headings and text. Translate rather than re-research, but flag anything you are unsure of; names of works and places should follow the usage of the target language. Then build, audition voices, record, check, publish as a separate guide (its own URL). One project = one language: a bilingual toggle is not supported.

## Limits

- Right-to-left languages (Arabic, Hebrew, Persian) are not supported by the page template; say so rather than shipping a broken layout.
- Highlighting follows sentence units, so text with no sentence punctuation (some lists, headings) is one unit.
- Mixed-script text (Latin names inside Chinese or Japanese) is read by the voice as best it can; `orig:` keeps such names out of the narration.
