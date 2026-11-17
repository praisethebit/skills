---
name: writing-for-agents
description: Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.
---

Reference for any document an agent reads: a skill, an `AGENTS.md` / `CLAUDE.md`, a doc reached by a pointer. The same levers make each one predictable. The agent follows the same _process_ each run.

For a skill, also read [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md): frontmatter, invocation choice, router skills.

## Context pointers

A **context pointer** is a reference in the agent's context that names out-of-context material and the condition to reach it. A skill description is one. A line in `AGENTS.md` that names a doc is one. The pointer's _wording_, not its target, decides when and how reliably the agent reaches the material. If a must-have target sits behind a weak pointer, sharpen the wording first. Inline the material only if that fails.

A pointer states what the material is and lists the **branches** that trigger it (a branch is a distinct case, so runs take different paths). An always-loaded pointer costs tokens on every turn, so prune it hard:

- **Front-load the leading word.**
- **One trigger per branch.** Merge synonyms of one branch.
- **Cut identity the body already carries.**

## The two loads

- **Context load**: always-loaded material (an `AGENTS.md` line, a skill description) costs tokens and attention every turn, whether or not it fires.
- **Cognitive load**: the human must know which documents exist and when to use each. Spend it where human judgement matters. Remove it where it does not.

Material behind a pointer costs only the pointer line. Material with no pointer costs cognitive load only.

## Information hierarchy

A document has **steps** (ordered actions) and **reference** (rules and facts used on demand). Rank each piece by how soon the agent needs it:

1. **In-file step**: what the agent does, in order.
2. **In-file reference**: used on demand. A flat set of peer rules is fine.
3. **Disclosed reference**: a separate file behind a pointer, loaded only when the pointer fires.

Too little disclosure bloats the top. Too much hides what the agent needs. **Progressive disclosure** moves material down the ladder to keep the top legible. The test is branching: inline what every branch needs, and put behind a pointer what only some branches need. Reference that should be disclosed buries the steps, so the agent may skip them.

**Co-location**: keep one concept's definition, rules, and caveats under one heading. Scattered material reads badly. (Duplication repeats one meaning in two places. Scattering splits one meaning across many.)

**Sprawl** is a document that is too long, even if every line is unique. Attention thins. Fix it with disclosure and with splits by branch or sequence.

## Steps and completion criteria

Each step ends on a **completion criterion**: the condition that shows the work is done.

- **Clarity**: the agent can tell done from not done. A vague bound ("understanding reached") causes **premature completion**, because the visible later steps pull attention forward. First sharpen the bound. Only if it stays fuzzy _and_ you see the rush, hide the later steps with a split. A split hides steps only across a real context boundary (a hand-off or a subagent). An inline call does not.
- **Demand**: how much the criterion requires. "Every modified model accounted for" forces more legwork than "produce a change list". Demand also binds flat reference ("every rule applied").

The best criteria are checkable and exhaustive.

## When to split

A split spends one of the two loads. Split only when the cut earns it:

- **By sequence**: split when later steps tempt the agent to rush the current step. Do not merge sequences, because each step then sees what follows.
- **By invocation** (skills only): see [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md).

## Leading words

A **leading word** is a compact concept from the model's pretraining that the agent thinks with (_lesson_, _fog of war_, _tracer bullets_). Repeat it as a token, never as a sentence. It recruits priors the model already has. A coined word recruits none, so use an existing word first.

It anchors in two places: in the body (_execution_: the same behaviour each time) and in a pointer (_invocation_: the shared word in prompts, docs, and code links the agent to the material).

Replace spelled-out phrases with one word:

- "fast, deterministic, low-overhead" → _tight_.
- "a loop you believe in" → _red_ (the loop goes _red_ on the bug, or it does not).

Find restatements that a leading word can retire.

**Negation** is the failure mode: a prohibition puts the banned behaviour into context and makes it _more_ likely. State the target behaviour ("write one-line comments"). Use a prohibition only as a hard guardrail that you cannot phrase positively, and pair it with the positive target.

## Match the form to the failure

A rule in the wrong form does not stop the failure, and the text grows. Name the failure first. Then pick the form:

- **A discipline failure** (the agent knows the right action and skips it): write a prohibition with its reason. Pair it with the positive target, as the Negation paragraph above requires.
- **A wrong output shape**: write a positive recipe. Show the shape that the output must have. A prohibition here puts the wrong shape into context.
- **A forgotten element**: add a required slot to a template. An empty slot shows the gap. A rule that says "do not forget X" does not.

## Pruning

- **Single source of truth**: keep each meaning in one place. Duplication costs tokens and maintenance, and it inflates the meaning's rank.
- The **environment** is a source of truth too (`package.json` scripts, config files, directory layout, `--help`). A document that restates it is a **cache**. Cache only what the agent cannot find by looking: the unwritten convention, the reason for a choice, the gotcha.
- Check each line for **relevance**. A line fails if it never bears on the task or if it is stale. Without pruning, **sediment** builds: stale layers that stay because adding feels safe and removing feels risky.
- Hunt **no-ops**: an instruction the model already obeys pays load and changes nothing. The test is whether it changes behaviour against the default. Settle a dispute by running the document. Delete the whole sentence. A leading word too weak to beat the default (_be thorough_) is a no-op. Replace it with the concrete behaviour that you want (_check each call site_).
