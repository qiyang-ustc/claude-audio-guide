# Writing and sourcing the narration

The narration is what people hear while standing in front of the real thing, so it has to be accurate, listenable and honest about its limits. This file is the standard to hold every stop to.

## What each layer is for

Playback is cumulative: at depth 2 the listener hears level 1 and then level 2; at depth 3, all three. Write each layer to continue the story.

| Layer | Length | Job | Typical content |
|---|---|---|---|
| 1 Quick | about 1 min (150-250 words) plus a look-list | Make them look up, tell them what they are seeing | The hook, who/what/when in plain terms, "three things to look for" |
| 2 Standard | about 1-2 min | Why it matters | Backstory, commission or purpose, technique or construction, how it was received |
| 3 Deep | about 1-2 min | Where the debates are | Disputed attributions or dates, restorations, scholarship that changed the view, loose threads |

If a stop has little to say at level 3, leave level 3 out; a padded layer is worse than none. A stop may have fewer layers than the guide (the depth buttons then play what exists).

## Research standard

- Use sources you actually opened in this session: the site's or museum's own pages, Wikipedia and Wikimedia pages, university or institutional pages, reputable encyclopaedias. List exactly those URLs in `@src`. A URL you did not read is a claim you cannot back.
- Look for the numbers that people cite and check them in two places: dates, dimensions, counts, heights, prices of historical items. When two reliable sources differ, write "accounts differ" and give both (`The date is given as 1581-83 in one source and 1584 in another`).
- When sources are silent on something the story seems to need (who paid, where it hung before, the exact size), say so in one sentence ("The museum does not give the size") or leave it out. Do not fill the gap from memory or plausibility. This is the single most common source of confident-sounding errors.
- Hedge with the source's own confidence: "is traditionally attributed to", "is usually dated", "scholars have proposed". Do not strengthen a hedge; do not invent one either.
- Names, titles, dates, quotations, and anything about living people deserve a second look. Never put words in a real person's mouth.
- Opening hours, ticket prices, queue times and room numbers change. Keep them out of the spoken text. Put the official link in the site's `links` and a "check on site" line in `foot`. If you take room labels from an official map, name the map and its date in `foot`.
- Areas under construction or closed: say what the official page says and no more.

## A verification pass (do it for any guide longer than a few stops)

After drafting, hand each group's text and its listed sources to a fresh reviewer (a subagent, or you after a break) with this brief: "For every date, number, proper name, attribution and causal claim, find the supporting sentence in the listed sources. Report each claim as supported, unsupported or contradicted. Do not add new facts." Then soften or delete what is not supported. Typical catches: a duke's regnal number, a sitter's name stated as fact, an "oldest/first/only" claim, a restoration date, a year that appears in only one source.

## Writing for the ear

- Sentences of 8-25 words. A voice runs out of breath on 40. The build warns above 260 characters.
- One idea per sentence, the most important word near the end. Avoid stacked clauses and parentheses; turn the aside into its own sentence.
- Spell out what a voice might misread: regnal numbers ("Leo the Tenth", not "Leo X"), roman-numeral centuries in the language's usual form, unusual abbreviations. The language file already handles ranges (1485-1490), "c." and common units.
- Avoid foreign names in brackets after the English or Chinese name; put the original title in `orig:` where it shows in italics instead of being read aloud badly.
- Numbers: give a few, round them, and say them in a form that sounds natural ("a little over three metres").
- Directions: "to your left" depends on where they stand. Use landmarks and room numbers ("the room beyond the long corridor") and say "as you enter".
- No tables, lists of dates, or references to the text ("see below"): the listener cannot see them.
- Look-list items are short imperative or noun phrases, not full paragraphs: "The shadow under the left foot".
- The first sentence of level 1 should orient: what is in front of you and why they might care.

## Voice of the guide

State the tone from the interview and keep to it. A guide for a family uses vivid verbs and fewer dates; one for an enthusiast names the debate and the scholar. Write as a knowledgeable companion, not as the institution. Do not claim to be an official guide; the page footer says the narration is AI-written from public sources, and that disclosure stays.

## Copyright and permissions

- Paraphrase. Quote a short phrase at most, with attribution. Do not reproduce paragraphs from museum labels, books or articles, and never song lyrics or poems under copyright.
- Images: public-domain or CC0 only, from Wikimedia Commons via `fetch_commons_image.py`, which checks the licence label. Reproductions of old flat artworks are usually fine; photos of sculpture, buildings and people are usually the photographer's work.
- Do not scrape or copy a competitor's audio guide text.

## Language-specific notes

- English: British or American spelling to match the voice (`en-GB` vs `en-US`). Use "c." for circa; the splitter and normaliser understand it.
- Chinese: write full sentences ending in 。！？; put the original Latin-script name in `orig:` rather than in parentheses (the normaliser drops Latin-letter brackets so the voice does not stumble).
- Other spaced languages: see `languages.md` for the abbreviations and the word for "to" in number ranges that must be configured.

## Sizing

At about 15 characters per second (English; 4.3 for Chinese) a 1-minute layer is roughly 900 characters. A 60-stop, three-layer guide is around three and a half hours of audio and about 65 MB at the default bitrate; a 12-stop one is under an hour and 15 MB. Tell the user these numbers when they choose the coverage.
