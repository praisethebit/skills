---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, written as one issue file per ticket.
disable-model-invocation: true
---

# To Tickets

## Opus guard

Do this check first, and again at the start of each turn until the skill ends. The skill ends when the tickets are published. Your system prompt names your model. If the model is not Opus and not Fable, stop. Do not do the next step. Tell the user: "This skill needs Opus or Fable. Press `s` in `/model`, pick Opus (the default) or Fable, then send your last message again."

Why: a `model:` key in a skill lasts for one turn only. Each reply of the user then goes back to the session model.

## Task

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Use the `Explore` agent for the search: it runs on Haiku and returns file paths and line numbers. Read the files that the design depends on yourself. Ticket titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

#### Failure modes from `## Decisions`

When the source is an issue, find the labels `Picked failure modes:` and `Declined failure modes:` in its `## Decisions`. When a list is missing, or the source is not an issue, place nothing and continue.

- **Picked.** Place each picked failure mode as an acceptance criterion in exactly one ticket, with a proof. Its guard is mandatory. It counts in the maximum of 6 criteria of that ticket.
- **Declined.** Write each declined failure mode as a line in `## Out of scope` of each ticket whose change can show it. Why: the review of a ticket reports a declined failure mode again when the ticket does not list it.

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Picked failure modes**: each picked failure mode that the ticket holds. Why: only the user can see that a pick is in the wrong ticket.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?

Iterate until the user approves the breakdown.

### 5. Publish the tickets

Write one file per approved ticket in the issue folder, at `<work folder>/issues/NNN-<slug>.md`. `NNN` is the next free number of the repo. Follow `~/.claude/issue-tracker.md`. Write the specs at `<work folder>/specs/<slug>.md`. Use the per-ticket file template below: one ticket per file, never a single combined file.

### 5a. Cold read

Do this before `ship`. Give the reader the absolute path of the ticket file. Read `~/.claude/skills/to-tickets/cold-read-ticket.md` and follow it.

1. Start one reader for each ticket in one message.
2. Show the user each paraphrase.
3. Sort each guess point: wording (fix the ticket), minor (decide, and write the decision in the ticket), or the user's. Ask all of the user's points in one `AskUserQuestion` round.
4. After the fixes, check each ticket again: `model` and `effort` match the mapping (the proofs and each other `opus` reason), it has a maximum of 6 criteria, it has a `seam` key that follows the rules of `## Seam` in the tracker doc, and each picked failure mode is still a criterion with a proof in exactly one ticket.
5. Start no second read. Each ticket gets one cold read.

Done when each ticket has a paraphrase (or a failed reader has an accepted gap, listed in the `## Answer` or the final message), and each guess point is fixed, decided or answered.

### 5b. Frontier, close and ship

Name the **frontier** in the final message: each ticket whose blockers are all done. `/implement` starts those tickets in later sessions.

If the source is an issue, close it after you publish the tickets. Do not close it while a picked failure mode is in no ticket: add the pick to a ticket first, and show the user that ticket. Append an `## Answer` section that lists the new tickets, then run `~/.claude/bin/close-issue NNN`. Then ship the new files and the closed issue with `ship --issues` and the `<work folder>/...` path of each file. Include each `edited:` path that `close-issue` prints.

<local-ticket-template>

```
---
project: <repo name>
status: open
category: enhancement
model: <opus|sonnet>
effort: <low|medium|high>
blocked_by: 018, 019
behavior_spec: <docs/spec/file.md, or none; only where the rule is on>
seam: <repo-relative paths, or none>
stage: next
feature: <feature name>
---
# <Ticket title>

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not a layer-by-layer implementation list.

## Acceptance criteria

- [ ] Acceptance criterion 1 (proof: <type>)
- [ ] Acceptance criterion 2 (proof: <type>)

## Out of scope

- The adjacent work that the ticket does not ask for, or "None."
```

In a repo where the `AGENTS.md` has the line ``Behavior spec: `docs/spec/`.``, write `behavior_spec: <files in docs/spec/>` (or `none` for a ticket with no behavior change), and write each criterion that states what the product does as a behavior criterion. Read `## Behavior spec` in the tracker doc for the form. Write `seam` in every ticket by the rules in `## Seam` of the tracker doc. Write `stage: next` in every ticket. Write the proof type of each criterion from the list in `~/.claude/issue-tracker.md`. Write `model` and `effort` by the mapping in the same doc. In `## Out of scope`, list each adjacent change that the implementer could do by mistake. Write `feature` when the run makes 2 or more tickets. Omit `blocked_by` when the ticket has no blocker. Write a value with quotes only where YAML needs them (for example `blocked_by: "019"`).

</local-ticket-template>

Avoid specific file paths or code snippets: they go stale fast. Exception 1: the `seam` key holds paths. Exception 2: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.
