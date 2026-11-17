---
name: add-issue
description: Add one issue to the repo's issue tracker from a short request, and ship it. Use when the user asks to open, add or create an issue, or starts the request with "add idea".
model: opus
argument-hint: <text>
---

Add one issue for: $ARGUMENTS

Each step ends on its completion criterion.

1. **Read.** Read the repo's issue tracker doc. Run `~/.claude/bin/next-issue --claim` to get the next free number. Why: `--claim` keeps a parallel session from getting the same number. If you cannot tell what the issue is about, ask the user one question. Done when you have the next free number and the subject.
2. **Look.** Use a maximum of 8 searches or reads in the code. When a review finding is the source, name the class of the gap and list all members of the class. Do not name only the one case that the review found. Done when you can name the files that the issue touches, not the fix.
3. **Write.** Write the issue in the tracker's format, with a maximum of 6 acceptance criteria. When the issue has acceptance criteria, end each criterion with its proof, for example `(proof: unit test)`, and add an `## Out of scope` section after the criteria ("None." is valid). An idea card needs neither. Set `stage` by the stage rule below. For "add idea: X", write the idea as the title and one line of text. When the search cap ends before you find all members of the class, write the missing members as an open question. When a review finding is the source, put the class and all known members in the issue. In a repo where the `AGENTS.md` has the line ``Behavior spec: `docs/spec/`.``, write a behavior criterion and `behavior_spec` (a file named after a durable capability of the product, not after this work) only when a criterion states what the product does (form: `## Behavior spec` in the tracker doc). With no behavior criterion, write no `behavior_spec` key. Set `model` and `effort` with the rule in the tracker doc. Write each unknown as an open question. Done when the file exists.

   **Stage rule.** Use the first row that matches:

   | Case | `stage` |
   |---|---|
   | The user names the stage (`idea`, `backlog`, `spec` or `next`) | that stage |
   | The request is "add idea: X" | `idea` |
   | The issue has an open question, or a decision that only the user can make | `backlog` |
   | No open question, and the work needs more than 6 criteria or more than one seam | `spec` |
   | No open question, and a maximum of 6 criteria in one seam, each with its proof | `next` |

   For `spec`, write the decided facts in a `## Decisions` section: `/to-tickets` reads it. When you are not sure of the row, use `backlog`. Why: `/implement` stops on an issue that is not clear, and that stop costs one session.
4. **Ship.** If the work folder is a symlink, call `ship` with the `--issues` form and the `<work folder>/...` path of the issue file. Otherwise call `ship` with the issue file. The request to open the issue is also the request to commit. In an `/implement` session, stop after step 3: that session ships the file with its work. Done when the commit is pushed, or when the file waits for the `/implement` commit.
