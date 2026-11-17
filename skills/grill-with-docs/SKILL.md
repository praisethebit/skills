---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---

## Opus guard

Do this check first, and again at the start of each turn until the skill ends. The skill ends after the `ship` call of the issue file. Your system prompt names your model. If the model is not Opus and not Fable, stop. Do not do the next step. Tell the user: "This skill needs Opus or Fable. Press `s` in `/model`, pick Opus (the default) or Fable, then send your last message again."

Why: a `model:` key in a skill lasts for one turn only. Each reply of the user then goes back to the session model.

## Start

Call the Skill tool twice, for "grilling" and "domain-modeling".

## End of the grill

Do this step only after the user confirms that you reached a shared understanding.

1. Find the issue of the grill. If the grill has no issue number, make one with the `add-issue` skill first.
2. Write the decisions in a `## Decisions` section of the issue.
3. If the work fits one ticket (a maximum of 6 acceptance criteria and one seam, with each picked failure mode counted as one criterion), add the acceptance criteria. Write each failure mode that the user picked in the last round as an acceptance criterion: its guard is mandatory. End each criterion with its proof in parentheses, for example `(proof: unit test)`. Add an `## Out of scope` section after the criteria. List each failure mode that the user declined and the adjacent work that the ticket does not ask for. Write "None." only when both are empty. The tracker doc lists the proof types. Then set the `model` key and the `effort` key (replace each if it exists), after the proofs are written. Use the mapping in the tracker doc (`~/.claude/issue-tracker.md`). Set `stage: next`. In a repo where the `AGENTS.md` has the line ``Behavior spec: `docs/spec/`.``, also write `behavior_spec` (the files in `docs/spec/`, or `none`) and write each criterion that states what the product does as a behavior criterion. Read `## Behavior spec` in the tracker doc for the form.
4. If the work does not fit one ticket (also when the picked failure modes bring the count above 6), set `stage: spec`. Write two lists in `## Decisions`, with these fixed labels: `Picked failure modes:` and `Declined failure modes:`. `/to-tickets` finds the lists by these labels and places them.
5. For a one-ticket result (step 3), run a cold read before `ship`. Read `~/.claude/skills/to-tickets/cold-read-ticket.md` and follow it for the issue file. Show the user the paraphrase. Sort each guess point: wording (fix the ticket), minor (decide, and write the decision in the ticket), or the user's (ask all in one `AskUserQuestion` round). Start no second read. After the fixes, check `model` and `effort` against the proofs again. Done when each guess point is fixed, decided or answered. Give the reader the absolute path of the issue file.
6. Ship the issue file with `ship --issues` and the `<work folder>/...` path of the issue file.
