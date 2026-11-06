# Interview guide

The aim is a complete `guide.json` after two short rounds of questions, with the user feeling asked rather than interrogated. Read this when you start a new project or when an existing user wants to reconfigure.

## Ground rules

- Ask in the user's own language. The guide's language is a separate question.
- One free-text opener in plain chat, then at most two rounds of multiple-choice questions. Each round is one AskUserQuestion call (max 4 questions, 2-4 options each, header max 12 characters, recommended option first with "(Recommended)"). The tool adds an "Other" box by itself, so never add one.
- If AskUserQuestion is not available, print the same questions as a numbered list with the options lettered and say "reply with e.g. 1a 2b 3a, or 'defaults'".
- Questions the user already answered are skipped. Questions whose answer is obvious from context (the user wrote in Spanish, so narration is Spanish) are stated as a default instead of asked: "I'll write it in Spanish; tell me if you'd rather not."
- Finish with a short summary and ask for a go-ahead. After that, do not ask more questions unless a real fork appears (for example the sources contradict each other on something that decides the scope).

## Opener (plain chat)

Ask in one message, adapting the wording to what you already know:

> What should the guide cover, and where? Roughly when are you going and how long will you spend there? And who will be listening: just you, or others who know less or more than you?

Listen for: the exact sites (a museum, a district, a route), the date and time budget (a 4-hour visit supports about 40 minutes of Quick narration or far more of Deep), the audience (first-timer, enthusiast, children), constraints (mobility, indoor/outdoor, offline use), and the user's language.

## Round 1: shape of the guide

Four questions in one call. Adapt the options to the subject; these are the defaults.

1. Header `Language` - "Which language should the narration be in?" Options: the user's own language (Recommended), English, and one or two other likely ones (the "Other" box covers the rest). Follow up in plain text only if the answer is unusual (right-to-left languages are not supported by the page template).
2. Header `Depth` - "How many depth layers should each stop have?"
   - "Three: Quick, Standard, Deep (Recommended)": about 1, 2 and 3 minutes of narration per stop, listener chooses how far to go.
   - "Two: Quick and Deep": half the writing and recording.
   - "One: a single narration": simplest; the depth buttons disappear.
3. Header `Coverage` - "How much should it cover?"
   - "Highlights, 10-15 stops (Recommended)"
   - "A full route, 30-60 stops": many hours of audio; recording and review take correspondingly long.
   - "One place in depth, 5-8 stops"
4. Header `Images` - "Should stops have pictures?"
   - "No images (Recommended)": nothing to license, the page is tiny.
   - "Public-domain images from Wikimedia Commons": found and licence-checked by the fetch script; works best for old paintings, maps and documents.
   - "I will supply my own": put JPEGs in `img/` that you have the right to publish.

## Round 2: voice, pace, output

Ask after the outline is agreed (Step 2) or together with round 1 if the user is in a hurry.

1. Header `Voice` - "How should the narration be recorded?"
   - "Natural neural voice via Edge (Recommended)": free, no key, many languages and voices; the text is sent to Microsoft's servers by an unofficial service.
   - "Offline macOS voice": nothing leaves the machine; much more robotic.
   - "My own TTS or cloud voice": the user supplies a command or key (see `tts-and-voices.md`).
   - "No recordings": the page reads the text with the phone's own voice.
2. Header `Pace` - "How fast should it speak?" "Normal (Recommended)", "A little slower (-8%)", "A little faster (+8%)". (Listeners can also change speed on the page.)
3. Header `Tone` - "Who is it for?" "Curious first-timer (Recommended)", "Keen enthusiast: more detail and debate", "Family with children: shorter, vivid, fewer dates", "Practical: orientation and logistics first".
4. Header `Publish` - "Where will it live?" "Just files on this computer (Recommended)", "A zip I can send around", "A static host I already use", "A shareable Claude artifact link (public to anyone with the link)".

## Voice audition (after the writing exists)

Generate three or four clips (`voice_samples.py`), send them, then ask one question:

- Header `Pick voice` - "Which voice sounds best for this guide?" Options are the candidate voice names with a short note (for example "en-GB-SoniaNeural: female, British"). Add "None of these: try others".

## Summary to confirm

Print this before the long work and wait for a yes:

```
Guide: <title>          Language: <narration> (page: <ui>)
Places: <site 1>, <site 2>...      Layers: <names>
Stops: about <n>        Images: <none | public domain | own>
Voice: <engine, name, pace>        Publish: <choice>
Tone: <audience>        Sources: official site + Wikipedia + scholarly pages, listed per stop
```

## Reconfiguring an existing project

Read `guide.json`, show the summary above from it, then ask only "What would you like to change?" with options matching the common requests: a different voice, another language (copy the project, see `languages.md`), more or fewer stops, change layers (needs rewriting or deleting layers), republish. Treat each as its own small workflow; do not re-run the full interview.
