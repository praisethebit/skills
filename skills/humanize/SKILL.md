---
name: humanize
description: Write or improve any text that a human reads, for example a README, guide, ADR, spec, research note, PR description or GitHub comment. Use for new text or a rewrite. Not for skills, AGENTS.md or CLAUDE.md (use writing-for-agents).
---

Write so a tired engineer understands the text on the first read. Apply the 3 top rules and the 4 layers. Then remove the AI patterns. The `adhd-ste` chat shape does not apply to a doc: add no "Next action" lines or step counters.

Based on `technical-writing` and `unslop` of `pstack` (MIT). See `NOTICE.md`.

## Rewrite

- Keep each fact. Add no fact, name, number or citation. When a fact is missing, ask the user.
- Write no more words than the source. Before the edit, copy the source and count it with `wc -w`. After the edit, count the result. When the result has more words, cut words that do no work until it has the same number or fewer.
- Before you edit a file that is not in git, or has uncommitted changes, copy it to the scratchpad.

## Top rules

- **Cut every word that does no work.** If the sentence survives without the word, remove the word. "In order to" is "to". "It is important to note that" is nothing.
- **Use the short, everyday word.** "Use", not "utilize". "Help", not "facilitate". "Do", not "perform".
- **When a rule makes a sentence worse, fix the sentence another way or leave it alone.** A sentence that follows each rule and sounds like a machine wrote it has failed.

The codebase is the word list. Write the real symbol, file, flag or command name, not a synonym. Do not invent jargon. Use the words a developer says out loud: "move", "delete", "a budget that only decreases".

Use a numbered list for a sequence and a table for a comparison.

## Layer 1: pick one doc type

One doc has one type. Two questions pick it. Does the content inform action or understanding? Does it serve learning or work?

- Action and learning: **tutorial**. Open with what the learner will build. Each step gives a visible result, and you say what the learner sees. Explain in one clause and a link.
- Action and work: **how-to**. Solve a problem that a person has. Assume competence. Give action only, and link background. Name the guide by the task: "How to calibrate the radar array".
- Understanding and work: **reference**. Describe only. No instruction, no opinion, no hedging. Mirror the structure of the thing described.
- Understanding and learning: **explanation**. One bounded topic. Give context: decisions, history, constraints, alternatives. Opinion is allowed here only.

Do not mix types. Split the doc and link the parts. A README states what the project is, how to install it and how to use it. An ADR keeps the `domain-modeling` format.

## Layer 2: sentences to the reader

- Write to "you" in the present tense. Use "will" only for later events.
- Name the actor: "the compiler checks", not "is checked".
- Write instructions as commands: "Click Submit."
- Put the condition before the instruction: "To delete the document, click Delete."
- Put the common case first and the exceptions after.
- Sound like a knowledgeable friend. Never write "simply", "easy" or "quickly" in a procedure.
- Make a heading carry the point. Use sentence case, one h1 and no skipped levels. A task heading is a verb phrase. A concept heading is a noun phrase.
- Link with words that say where the link goes. Never write "click here".
- Introduce a list with a full sentence. Keep the items parallel.
- Put code in code font and UI elements in bold. Use serial commas. Drop "etc.".

## Layer 3: one statement at a time (STE)

- Write one instruction in each sentence.
- Keep instructions to about 20 words and other sentences to about 25 words. These are guides.
- Put the warning or condition before the step it guards.
- Keep "the" and "a": "Remove the backup file" reads one way.
- Give each word one meaning. Use one word for one action: "start", not "start" and "initiate".
- Write procedures as direct commands in the active voice.
- Avoid "-ing" words where a different form works.

## Layer 4: one reading only (Global English)

- Keep "only" and "not" next to the word they change.
- Break up noun strings: "the tool that checks the proto-import budget".
- Make each "it", "they" and "this" point at one thing. Repeat the noun when in doubt. Never use "this" or "which" for a whole clause.
- Keep the verb in each clause. Keep small words such as "that".
- Repeat the article in a series when two things are meant: "the client and the host".
- Say what "and" or "or" joins when the sentence can group two ways.
- Use periods, not semicolons. Replace an em dash with a new sentence.
- Make text in parentheses a full unit. Write no "(s)" plurals and no slashes: "a, b, or both".
- Call each thing by one name in the whole doc.
- Skip idioms, Latin abbreviations and metaphors.

## Vary the rhythm

A doc can follow each layer and still read like a machine wrote it. Mix short and long sentences. A short sentence lands a point. A long sentence carries a fact with its condition. Split a sentence that carries two thoughts. Keep a long sentence that carries one.

Give a view where the type allows it. Explanation weighs trade-offs. Reference stays dry. Be specific: not "schema changes can cause issues" but "a column rename fails the build".

## AI patterns to remove

**Content**
- Superficial "-ing" phrases: "highlighting", "ensuring", "showcasing". Delete them or name the real source.
- Vague attributions: "Experts believe". Name the source or delete.

**Language**
- AI vocabulary: additionally, crucial, delve, enhance, foster, garner, interplay, intricate, landscape, pivotal, showcase, tapestry, testament, underscore, vibrant. Use plain words.
- Fancy "is": "serves as", "stands as", "boasts", "features". Write "is" or "has".
- "Not just X, but Y." State the point.
- Rule of three. Use the natural number of items.
- Synonym cycling: main character, hero, central figure. Pick one word.
- False ranges: "from X to Y" with no real scale. List the topics.

**Style**
- Em dashes. Write a new sentence.
- Colons as mid-sentence connectors. Keep a colon only before a list or an example.
- Too much bold. Do not bold each name or acronym.
- Inline-header lists, where a bold label restates the line ("**Performance:** Performance improved"). Write prose. A bold lead-in with new detail is fine.
- Title case headings. Use sentence case.
- Decorative emojis. Remove them.
- Curly quotes. Use straight quotes.

**Chat leftovers**
- "I hope this helps!", "Certainly!", "Let me know if". Remove.
- Sycophancy: "Great question!". Answer directly.

**Filler**
- "In order to" is "to". "Due to the fact that" is "because".
- Hedging: "could potentially be argued that it might" is "may".
- Generic conclusions: "The future looks bright." State a fact or a plan.

**Jargon**
- Abstract metaphor nouns: substrate, wedge, vector, locus, nexus, bedrock, scaffolding, paradigm, modality, gold-plating, ratchet, evacuate (for moving code), endgame, north star, flywheel, "API surface". Use the concrete word.

**Plain speech**
- Say what it does, not how it feels. "SQL you can read" names a feeling. "`.toSQL()` returns the exact string sent to the database" names the mechanism. If a sentence has no instruction, fact or number, cut it. If it fits unchanged in another project, cut it.
- Split a dense sentence if the reader must go back to parse it.
- Use the active voice. Passive is fine only when the actor is unknown.
- Replace an adverb with a stronger verb or a number: "significantly improves" is the measured change.
- Use the plain word: "utilize" and "leverage" are "use". "Numerous" is "many".
- Mannered prose: aphorisms, rhetorical fragments, personified code, figurative verbs. Write the literal phrase.
- Over-compression: dropped articles, verbless fragments, arrows. "Parser rejects bad date → exit 2" is "The parser rejects a bad date, exits with code 2, and writes nothing."

## Example

Before:

> Configuration of the proto import ratchet budget tool parameters is performed via budget.json. Note that it's important to remember that running with --write, which updates the committed budget to reflect the current count, should only be done when lowering it. If exceeded, CI fails.

After:

> `budget.mjs` reads the committed budget from `budget.json` and counts the files that import protos. If the count exceeds the budget, CI fails. Run `budget.mjs --write` only to lower the budget.
