# Issue tracker: Local Markdown

This is the shared tracker doc for all repos. Each repo's `AGENTS.md` points to `~/.claude/issue-tracker.md`. Read `~/.claude/local/issue-tracker.md` when it exists, and follow its steps.

Issues and specs live as markdown files in the work folder.

## Where the files are

- The work folder holds the issues, specs, research and audit logs of a repo. The first line ``Work folder: `<name>`.`` in the `AGENTS.md` of the repo names it. `~/.claude/bin/work-folder` prints the name. With no such line, the work folder is `planning`. The issue folder is `<work folder>/issues/`.
- A work folder can be a symlink into another git repo (the issue repo). Then the issue files are in the issue repo, not in the code repo. `ship` commits both repos in one call. In the issue repo, it commits only the `<work folder>/...` paths that you pass. Use `ship --issues` with the `<work folder>/...` paths for a change with no code paths.

## Conventions

- Open issues live in `<work folder>/issues/NNN-<slug>.md`. Closed ones (`resolved`/`wontfix`) move to `<work folder>/issues/done/`.
- `NNN` is a zero-padded number for this repo. A new issue takes the highest number across both folders + 1. Numbers are never reused. Refer to an issue as `#007`. Refer to an issue in another repo as `other-repo#160`.
- A file uses YAML frontmatter at the top of the file. Then comes `# <title>`.
- Write a frontmatter value with quotes only where YAML needs them: `status: open`, `blocked_by: 018, 019`, `was: other-repo#123`, but `blocked_by: "019"`. Then a change of one value changes one line.
- Keys (frontmatter keys are lowercase, and a space becomes `_`): `project` and `status` (`open`, `resolved` or `wontfix`) always. Optional: `category` (`bug|enhancement`), `model` (`opus|sonnet`), `effort` (`low|medium|high`), `blocked_by` (`018, 019`; quote a lone number, such as `"026"`, because YAML reads `026` as the number 26), `stage` (the planning stage: `idea`, `backlog`, `spec`, `next` or `done`), `feature` (the name of the feature; set it only when 2 or more open issues share it), `created` (`YYYY-MM-DDTHH:MM:SS` in local time, set by `ship` on the first commit of the file; do not write it by hand), `closed` (`YYYY-MM-DDTHH:MM:SS` in local time, set by `close-issue`), `spec` (`<work folder>/specs/<slug>.md`), `behavior_spec` (one or more files in `docs/spec/`, for example `docs/spec/sync.md` or `docs/spec/sync.md, docs/spec/login.md` (a comma list, like `blocked_by`), or `none`; see `## Behavior spec`), `was` (`other-repo#NNN`, the old number of a moved issue), `host` (the one host that the work changes, for example `host: docker01`; only a repo that has hosts uses it). An old file keeps `YYYY-MM-DD` in `created` or `closed`. Every reader must accept both forms.
- `model` is the recommended model for the session that implements the issue. Set it when you create the issue. `opus`: a study, an idea, a decision, or a root-cause search. Also use `opus` when the cause is not known. Also use `opus` when the proof is an app device proof. `sonnet`: a clear ticket with acceptance criteria, when the ticket has no other `opus` reason. This covers a local proof and each proof that is not local, except an app device proof. A local proof is a unit test, a local script, a browser test on a local build, a lint or hook check, or a read of changed text (a docs-only change).

  A proof is not local in each of these cases. Each case gives `sonnet`, except an app device proof, which gives `opus`:

  - A server host or a VM.
  - An app device proof: the app that the repo builds runs on an emulator or a real device. This case gives `opus`.
  - A home device proof: a home device, such as a phone, a sensor or a button, shows a result, and the repo builds no code for the device.
  - A read from a hosted API, such as a GitHub API call.
  - A scripted DNS check, or a check of a live route.
  - A proof that waits for a later outside event.
  - A load test on a real host.

  Also use `opus` for a root-cause search of a network or timing failure.

  Also use `opus` for a migration (data, schema or config format) and for a performance optimization, also with a clear spec and a local proof. Why: a clear spec is not sufficient for these.

  `haiku` is not a value for an implement session. Why: an `/implement` session is a long loop, and Haiku is weak in long loops. When you are not sure, use the stronger model. A major refactor is split by `/to-tickets`, so the rule has no `fable` value.

- A ticket (an issue with acceptance criteria) has two more parts:
  - `## Out of scope` comes after `## Acceptance criteria`. It lists the adjacent work that the ticket does not ask for. "None." is valid. Why: a cheap model tends to do adjacent work, and the review must not report an item that the user declined.
  - Each acceptance criterion ends with its proof in parentheses, for example `(proof: unit test)`. Why: the planner needs the proof to set `model`, so the implementer does not choose it.
  - Proof types, local: `unit test`, `local script`, `browser test on a local build`, `lint or hook check`, `dry run or validate step`, `read of the changed text`. Not local, and the issue gets `sonnet`: `server host or VM`, `home device` (a home device, such as a phone, a sensor or a button, shows a result, and the repo builds no code for the device), `hosted API read`, `DNS or live route check`, `later outside event`, `load test on a real host`. Not local, and the issue gets `opus`: `app on emulator or device` (the app that the repo builds runs on an emulator or a real device). The old name `emulator or device` gives `opus`.
  - An idea card has neither part.

- `effort` is the recommended effort for the session. Each writer of `model` also writes `effort` in each new issue, so a session does not depend on the saved default effort. The mapping:

  | Case | `model` | `effort` |
  |---|---|---|
  | Small change, no decisions, local proof | `sonnet` | `low` |
  | Clear ticket, local proof | `sonnet` | `medium` |
  | Migration (data, schema or config format) or performance optimization | `opus` | `medium` |
  | Proof is not local, and not an app device proof | `sonnet` | `medium` |
  | App device proof | `opus` | `medium` |
  | Study, idea, decision, root-cause search, cause not known | `opus` | `high` |

  When 2 rows match, use the row with the higher `effort`. When rows with the same `effort` give different models, use `opus`. A not-local proof gives `sonnet` only when the ticket has no other `opus` reason: a root-cause search, a migration, a performance optimization, a study or a decision. A ticket with the old proof name `emulator or device` gets the row "App device proof".

- Escalation: `/implement` stops when one criterion still fails its check after 2 fixes. It recommends the next step of this order: a test of the assumption that the 2 failed fixes share (one observation; a false assumption gives one more fix), then more effort (`low` → `medium` → `high`), then `sonnet high` → `opus medium` → `opus high`. After `opus high`, the issue goes back to an Opus planning session. The session writes the new `model` and `effort` in the issue file before it stops.
- Each stage names the next action of an issue. Next means "ready", not "few". An issue can skip a stage.

  | `stage` | Meaning | Next action |
  |---|---|---|
  | `idea` | The user is not sure that they want it | The user decides |
  | `backlog` | The user wants it, and nobody discussed it yet | `/grill-with-docs` |
  | `spec` | Clear, and too big for one ticket | `/to-tickets` |
  | `next` | Clear and ready | `/implement NNN` |
  | `done` | Closed | None |

- Who changes `stage`:
  - `add-issue` writes the first stage of an issue, by the stage rule in step 3 of the skill: `next` for an issue with no open question that fits one ticket, `spec` for an issue with no open question that is too big for one ticket, and `backlog` for each other issue. "add idea: X" writes `idea`.
  - The end of `/grill-with-docs` writes `next` or `spec`, after the user confirms the shared understanding.
  - `/to-tickets` writes `next` on each ticket, and closes the source issue with an `## Answer` that lists the new tickets.
  - `close-issue` writes `done`.
  - The user changes any other stage by hand. An agent changes `stage` in no other case, unless the user tells it to. Do not set `done` by hand: only `close-issue` closes an issue.
- Example of the frontmatter:

  ```
  ---
  project: example
  status: open
  model: sonnet
  effort: medium
  stage: backlog
  ---
  # Title
  ```

- Specs live at `<work folder>/specs/<slug>.md`.
- Comments go at the bottom of the file under a `## Comments` heading.
- To close an issue as `resolved`: append an `## Answer` section that says what changed. An issue that `/implement` closes also has a `### Rulings` list in the Answer (one line for each ruling: what, why, cost if wrong; or "None."), then run `~/.claude/bin/close-issue NNN` in the repo. The command is in `~/.claude/bin/`, the same as `ship`. It reads both formats. It sets the status to `resolved`, `stage` to `done` and `closed` to the date and the time (`YYYY-MM-DDTHH:MM:SS`). It ticks every `- [ ]` above `## Answer`, and moves the file into `<work folder>/issues/done/`. It removes the closed number from `blocked_by` in the other open issues. It does not commit. For `wontfix`, write the `## Answer` with the reason, then run `~/.claude/bin/close-issue --wontfix NNN`.
- An issue is only `resolved` when its lasting facts are in the README, the config, the behavior spec (a behavior fact) or a `why:` comment (only for a fact about an external tool that the code cannot show, or about our own design that no test name or doc can hold). The Answer names each place as a code-format path, for example `docs/recovery.md`. A rebuild never reads `done/`.
- In an issue file, write a repo file or a different issue in code format, not as a Markdown link. Why: a relative link breaks when `close-issue` moves the file to `done/`, or when a parallel session renames the target.

## Behavior spec

A ticket that changes what a product does also changes the behavior spec of that product, in the same commit.

- **Which repos.** The rule is on in a repo when its `AGENTS.md` has the line ``Behavior spec: `docs/spec/`.`` In a repo with no such line, nothing changes.
- **File.** One file for each capability: `docs/spec/<capability>.md`. The name of a capability is a durable behavior of the product (for example `sync`), not the work of one ticket. A new file starts with a title line (`# <Capability>`) and one sentence that says what the capability covers. Then the entries follow, with one empty line between 2 entries. The implementer creates the folder and the file when they do not exist.
- **Entry.** One plain sentence in the form "When (condition), the app (result).", then one line that starts with `Why:` and gives the reason. The result is the effect that the user or an outside system sees. An outside system is a system that the product talks to, for example the Server, Android or a different app. A mechanism is a step that the app takes only to get the result, also when an outside system can see the step (for example "with no logoff"). A mechanism goes in the `Why:` line, not in the sentence. When the text before the `Why:` line has 2 sentences, it becomes 2 entries. A `Why:` line can name an ADR. It names no issue number, because the issues can be private. A changed behavior replaces its entry, and a removed behavior removes its entry. Git keeps the history.
- **Content.** Behavior only. The test: if the implementation can change with no change that the user or an outside system can see, the fact does not go in the behavior spec.
- **Behavior criterion.** An acceptance criterion in the sentence form of an entry. The planner uses this form for each criterion that states what the product does, and for no other criterion. One behavior criterion can have 2 entries.
- **One home for each fact.** Behavior spec: a behavior and its reason. ADR: a structural decision that is hard to reverse. README: setup and use. `GLOSSARY.md`: a term.
- **Key `behavior_spec`.** `/to-tickets` and the end step of `/grill-with-docs` write the key in a repo where the rule is on: the files in `docs/spec/`, or `none` for a ticket with no behavior change. `add-issue` writes the key only when it writes a behavior criterion. With no behavior criterion, it writes no key, and a later grill adds it.
- **Implementer.** Step 2 of `/implement` writes one or 2 entries for each behavior criterion, in the file of its capability among the files that the key names. The `## Answer` names the spec file as the place of each behavior fact.
- **Old tickets.** A ticket with no `behavior_spec` key, or with `none`, gets no spec edit.

Open work: `ls <work folder>/issues`.

## When a skill says "publish to the issue tracker"

Create a new file `<work folder>/issues/NNN-<slug>.md` with the next free number.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. Match the number (`#007`, `007`) against the `NNN-` prefix in `<work folder>/issues/` or `<work folder>/issues/done/`.
