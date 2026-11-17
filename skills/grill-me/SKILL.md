---
name: grill-me
description: A relentless interview to sharpen a plan or design.
disable-model-invocation: true
---

## Opus guard

Do this check first, and again at the start of each turn until the skill ends. The skill ends when the user confirms a shared understanding. Your system prompt names your model. If the model is not Opus and not Fable, stop. Do not do the next step. Tell the user: "This skill needs Opus or Fable. Press `s` in `/model`, pick Opus (the default) or Fable, then send your last message again."

Why: a `model:` key in a skill lasts for one turn only. Each reply of the user then goes back to the session model.

## Start

Call the Skill tool with "grilling".
