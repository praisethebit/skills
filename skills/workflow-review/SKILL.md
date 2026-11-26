---
name: workflow-review
description: Score the sessions in a time window and propose harness and workflow improvements.
disable-model-invocation: true
argument-hint: "[Nh | Nd | YYYY-MM-DD]"
---

## Opus guard

Do this check first, and again at the start of each turn until the skill ends. The skill ends when step 8 is done, or when step 2 finds 0 sessions. Your system prompt names your model. If the model is not Opus and not Fable, stop. Do not do the next step. Tell the user: "This skill needs Opus or Fable. Press `s` in `/model`, pick Opus (the default) or Fable, then send your last message again."

Why: a `model:` key in a skill lasts for one turn only. Each reply of the user then goes back to the session model.

## Task

Grade the workflow and the harness. Score the sessions in one window on 6 rubrics, compute 7 scores and `overall`, and propose changes. The goal is fewer tokens, simpler steps and better efficiency. Use evidence from the logs, not opinion. Everything runs on this machine: do not upload a transcript. Each step ends on its completion criterion.

Local extension: read `~/.claude/local/workflow-review.md` when it exists, and follow its steps.

Let `SKILL_ROOT` be the directory that holds this `SKILL.md`. Shell variables do not carry from one Bash call to the next: in each Bash call, write the absolute paths of `SKILL_ROOT` and `REPORT_DIR`, or set them again.

## Step 1: Scope

Ask with `AskUserQuestion`: "Which sessions should I score?" Options: this repo (recommended), all sessions, chosen projects. For chosen projects, ask for the paths. Each path must be a git repository.

Set the scope keys. "This repo" has one key: the absolute path of the main checkout of the repo (not a worktree or a subdirectory). "All sessions" has the key `all`. "Chosen projects" has one key for each repo: its absolute path.

## Window

Ask the scope first (step 1). Then set the window from `$ARGUMENTS`:

| Argument | Window |
|---|---|
| empty | from the saved time of the scope until now. With no saved time: all sessions |
| `Nh` (for example `6h`) | the last N hours |
| `Nd` (for example `3d`) | the last N days |
| `YYYY-MM-DD` | that day, local midnight to midnight |

State the window, in local time and in UTC, before step 2. With no saved time, state `all sessions (no saved time for <scope key>)`, with no time.

### Saved time

The file `~/.claude/state/workflow-review-last` is a runtime file. Each line is `<scope key><TAB><UTC timestamp>`, for example `/path/to/repo<TAB>2026-11-08T18:49:44Z`.

With an empty argument:

- One scope key: the window starts at the saved time of the key.
- Chosen projects: the window starts at the earliest saved time of the chosen repos. A repo with no saved time counts as `1970-01-01T00:00:00Z`, so the window covers all sessions.
- A key with no saved time means "never reviewed": the window covers all sessions, from `1970-01-01T00:00:00Z`.

Before step 2, run `date -u +%Y-%m-%dT%H:%M:%SZ` one time. Keep the output as `RUN_START`: the time that the run starts. It is not the start of the window. Do not run `date` again for the save.

Pass the window to the collector in one of these ways:

- Empty argument with a saved time: `--since "<saved UTC time>"`. Do not use `--window` with it. Do not round the time to `Nh` or `Nd`.
- Empty argument with no saved time: `--since 1970-01-01T00:00:00Z`.
- Explicit argument: `--window "$ARGUMENTS"`.

Create the run folder with `mktemp -d "${TMPDIR:-/tmp}/workflow-review-XXXXXXXX"`. Keep its absolute path as `REPORT_DIR`. Write no file in the user repo, except the report file and the `.git/info/exclude` line of step 7.

## Step 2: Collect

```bash
python3 "$SKILL_ROOT/scripts/collect_sessions.py" --out "$REPORT_DIR" <window flag> <scope flags> <test flags>
```

- Scope flags: `--repo PATH` for each project (the default is the repo of the working directory), or `--all-sessions`.
- Test flags: one `--test-pattern REGEX` for each test command that the `AGENTS.md` of each repo in scope names. With all sessions, read the `AGENTS.md` of each repo that has a session in the window.
- `--skills-dir PATH` adds a skill folder.

The collector skips each session that has the `/workflow-review` command in any user message. It also skips each headless `claude -p` session. The transcript of the session that started a `claude -p` run shows the run and its cost. Add `--include-headless` to collect them.

Read `$REPORT_DIR/inventory.json`. If it has 0 sessions, tell the user and stop. Done when the transcripts are in `$REPORT_DIR/transcripts/`.

## Step 3: Score

1. Print the session count and a token estimate (the total characters of the transcript files, divided by 4). Do not stop to ask. The user controls the cost with the window.
2. Split the sessions into batches of 5 sessions. Start one Sonnet subagent for each batch (`model: sonnet`), all in one message, so that they run in parallel.
3. Give each subagent the paths of its transcripts and these 6 rubrics, with absolute paths: `$SKILL_ROOT/scorers/outcome.md`, `efficiency.md`, `code-quality.md`, `test-quality.md`, `procedure-compliance.md` and `verbosity.md` in the same folder. Tell it to return, for each session and each rubric, the label, the score from the rubric table, and a reason of 1 to 3 sentences with the evidence. It changes no file.
4. A subagent that fails: start it again one time. If it fails again, tell the user which sessions have no score.

Done when each session has a result for each rubric.

## Step 4: Aggregate and verify

The main session does this step. Do not delegate it. Calculate each mean, each curve value and `overall` in one `python3` call, not by hand. The list below is the specification of that calculation.

- `raw_<rubric>` = the mean of the scores of a rubric over all sessions. Leave out `insufficient_evidence` results of `outcome`, `code-quality` and `test-quality`. If no session has evidence for a rubric, use 0.5 and say so.
- `curve(x) = 0.5 + 0.5 * x`. Apply it to the 6 raw means: `outcome`, `efficiency`, `code_quality`, `test_quality`, `procedure_compliance`, `verbosity`.
- `skill_coverage` = the fraction of sessions with at least one `Skill` tool call to an installed skill. Count the `Skill` calls in the transcripts. Do not use `skills_used` in `inventory.json`: it also counts a skill file that a session only read. It has no curve. It is 0 if no skill is installed.
- `overall = 0.20 * outcome + 0.20 * efficiency + 0.15 * code_quality + 0.15 * procedure_compliance + 0.10 * test_quality + 0.10 * verbosity + 0.10 * skill_coverage`
- A failed session has at least one score below 0.5 (an `insufficient_evidence` result does not count). A change for a finding needs a score below 0.5 in two or more sessions, or one failure that proves a rule is missing.
- Verify each finding: open the transcript at the cited moment. Drop a finding that the transcript does not show.
- `top_findings`: the 3 patterns with the largest cost, each with a session and a moment.

Done when you have the 7 scores, `overall` and the verified findings.

## Step 5: Find repeated work (new tooling)

Use all sessions in the window, not only failed sessions. Look for:

- the same Bash command, or the same chain of calls
- the same user prompt
- the same user correction ("no, use X")
- the same call that the user denied or that asked for a permission

A candidate needs 3 or more occurrences in 2 or more sessions. Give each candidate one type: **skill**, **hook**, **script**, **permission** or **rule**. Check that no existing item has the same job. Done when each candidate has a count, an example, a type and the "no duplicate" check.

## Step 6: Propose changes

Read `$SKILL_ROOT/references/workflow-improvements.md` and follow it. A change can target a skill, `CLAUDE.md`, `~/.claude/workflow.md`, `AGENTS.md`, a hook, `settings.json` (for example a permission), or a new script or tool. Give each change the evidence, the owning surface and the exact diff. Order the changes with the largest saving first. For each finding or step 5 candidate that gets no change, write the reason. For each step 5 candidate that you recommend, write the diff or the new file, and give it a number in the same list. Do not change a file in this step.

## Step 7: Report

Set `REPORT_FILE`. The transcripts and `inventory.json` stay in `REPORT_DIR`.

1. Run `git -C <working folder> rev-parse --path-format=absolute --git-common-dir`. Keep the output as `GIT_DIR`. Its parent folder is the main checkout (also when the session runs in a worktree).
2. If the command fails, or `<main checkout>/.git` is not `GIT_DIR` (a bare repo or a submodule), set `REPORT_FILE` to `$REPORT_DIR/report.md`.
3. Otherwise set `REPORT_FILE` to `<main checkout>/.workflow-review/<YYYY-MM-DD-HHMM>.md`. Get the name with `date -d "<RUN_START value>" +%Y-%m-%d-%H%M` (local time): write the literal `RUN_START` value, because an unset variable gives midnight. Run `mkdir -p` on the folder. A second run in the same minute overwrites the file.
4. Run `mkdir -p "$GIT_DIR/info"`. Add the line `.workflow-review/` to `$GIT_DIR/info/exclude` (write the literal path), only when the file has no such line (check with `grep -qxF`). Change no tracked file.

Write `REPORT_FILE` with these 5 sections, in this order:

1. **Grade**: the 7 scores and `overall`.
2. **Top findings**: the 3 patterns from step 4.
3. **Change these**: the numbered changes from step 6, each with the evidence, the owning surface and the diff.
4. **New tooling**: the candidates from step 5, each with the count, the example, the type and the "no duplicate" check.
5. **Do not change**: each finding or candidate that gets no change, with the reason.

Write no HTML page, no PNG and no link. Give the grade and the top findings in chat, with the absolute path of `REPORT_FILE`. Done when `REPORT_FILE` exists and has the 5 sections.

Save the time only when the argument is empty. Why: a run of a past day would move the saved time to now and hide the sessions between. Do it after `REPORT_FILE` exists. For each scope key of the run, replace its line in `~/.claude/state/workflow-review-last` (or add it) with `<scope key><TAB><RUN_START>`. Save `RUN_START` (the start time of the run), not the end time. Create the folder `~/.claude/state` if it is missing. An explicit argument saves no time.

## Step 8: Apply

Ask the user which changes to apply (`AskUserQuestion` with `multiSelect: true`). The tool allows 4 options in a question: split the numbered changes, including the recommended candidates, into questions of 4 options. Apply only the selected ones. Validate each edit (for example `jq empty` on JSON). Commit the repo files with `commit-push`. A file outside a git repo stays on disk only: tell the user which ones. Done when each selected change is applied and validated.
