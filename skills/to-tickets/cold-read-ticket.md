# Cold-read prompt for a ticket

Give this prompt to one fresh subagent for each ticket. Use `subagent_type: general-purpose` and `model: sonnet`, also for a ticket with `model: opus`. Start all readers in one message. Fill the 3 values. Write each path as an absolute path. Give the subagent nothing else: no chat, no rules, no history.

Write `none` for Blocking tickets when the ticket has no `blocked_by`. Write the paths of the files of the tickets that it names, otherwise.

```text
You are the implementer of a ticket. You know nothing about the planning of this ticket.
Read this ticket in full: <ticket path>
Blocking tickets: <paths of the tickets in blocked_by, or none>
Repo: <path of the repo>
Do not change a file. Do not run a command that changes state.

You can read the repo, the same as the implementer. Read the blocking tickets before you report a guess.
Do not report a guess that the repo or a blocking ticket answers.

Plan the work as if you build the ticket. Write:
1. `Paraphrase:` a maximum of 3 sentences. What you will build.
2. One line for each guess point:
`<what you must guess> -> <what the ticket must say>`
A guess point is a term that no file defines, a missing input or result, an unclear order, a criterion with no proof, or a choice that changes the result.
If you have no guess point, write `NO GUESSES`.
```

A reader fails when it returns an error, no text, or a text with no `Paraphrase:` line. Start a failed reader one more time. A second failure is a blocker: follow the Blockers rule in `~/.claude/workflow.md`. Do not treat it as a result with no guess points.
