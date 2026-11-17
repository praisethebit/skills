# How we work (all repos)

Repo-specific rules are in each repo's `AGENTS.md` / `CLAUDE.md`. They override this file.

The work folder of a repo holds its issues, specs, research and audit logs. The tracker doc `~/.claude/issue-tracker.md` defines it. Read `~/.claude/local/<skill>.md` when a skill names it and the file exists.

## Workflow

1. Plan: `/grill-with-docs`, then `/to-tickets`, in one session on Opus (default) or Fable. Start it with `claude --model opus`, or press `s` in the `/model` picker. Plain `/model opus` saves Opus as the default. Pick Fable by hand for a large epic. `/grill-with-docs`, `/grill-me`, `/to-tickets`, `/audit` and `/workflow-review` stop when the model is not Opus and not Fable.
   1a. Size of a ticket: a maximum of 6 acceptance criteria, and work in one seam. Use approximately 800 changed lines as a guide. The fixed checks that a repo copies into each ticket do not count. When a feature needs fixed checks (for example a UI review), put them in one "Finish" ticket at the end of the feature, not in each ticket. A feature has a maximum of 4 tickets before its Finish ticket. A Finish ticket fixes a maximum of 6 findings, high severity first. Each other finding becomes a new ticket. The Finish ticket closes when each high-severity finding is fixed or has a ticket.
2. `/clear`. The default model is Sonnet.
3. Implement one issue per session: `/implement NNN`. The skill implements, reviews, closes and ships the issue. Then `/clear` before the next issue.
   3a. To implement 2 or more issues of one repo at the same time, start each extra session in its own worktree: `claude -w <NNN>`. Two sessions in one checkout can lose edits, because the `pre-commit` hook stashes all unstaged edits during a commit. `ship` pushes the worktree commit to `main`. After the session, run `git pull` in the main checkout. In a worktree session, write each path as a literal absolute path. Do not start a Bash call with `cd`, and do not use `git -C`, `env -C`, `bash -c`, `$(...)` or `git` in a loop. Why: Claude Code refuses these calls in a worktree, and each refusal costs one more turn.
4. Run `/workflow-review` one time at the end of an epic (all tickets from one `/to-tickets`). The review proposes a change only for a gap that happened in two or more sessions, or for one failure that proves a rule is missing (for example a breach of a protective rule).

## Blockers

- A blocker is anything that stops you from doing or testing a requirement: no connection, a missing tool, no access, a timeout after the one retry of the Long commands rule, an unclear result.
- When you hit a blocker, stop that requirement. State the requirement, the exact command or error, and what you tried. Then ask the user with `AskUserQuestion`. The options are: the user removes the blocker, the user gives another way, or the user accepts the gap. The user sees only the dialog: put each command and each step that the user must do in the question text, not only in the chat, a preview or a file.
- Do not skip, simulate, or silently drop a requirement. Do not close an issue with a requirement that you did not meet and prove. List each accepted gap in the `## Answer`.
- The user has admin on all machines. Do not assume a setting, service, or permission is locked, off, or impossible. Ask the user to enable, disable, or grant it.

## Long commands

- Run a command that can take more than 2 minutes with `run_in_background`, or give it an explicit `timeout`.
- Search a named folder (`~`, `~/.claude`, `~/.local` or the app folder) with `timeout 30`. A search from `/` stops at the 120 s limit.
- Use `ssh -o ConnectTimeout=10 -o ServerAliveInterval=15`. Use `timeout 60` before each `adb` command.
- If a command times out, exits with code 124, or "was moved to the background", find the cause. When the cause is clear and you can remove it (for example a `timeout` that is too short), run the command one more time with the fix. If the second run fails, or the cause is not clear, it is a blocker: report it. Do not retry in a loop and do not continue as if it passed.
- Run each live write as its own Bash call. A live write changes a host, a cluster, a secret store or GitHub, uses `sudo`, or installs from the network. The auto-mode classifier can deny it, and a denial stops each command in the same call.

## Review rules

These rules apply to each code review (`/code-review`). Zero findings is a correct result.

1. Report a finding only if it can break behavior or makes a statement false. Name the file, the line and the failure.
2. The close step fills `## Answer`, the open boxes, `status` and `stage`. Do not report them. A criterion with no proof stays a valid finding.
3. Report no style points.
4. Report no wording, size or metadata of the issue. Report the issue only if it asks for something false or impossible.
5. When the issue names a file in `behavior_spec`, a behavior criterion with no entry in the diff is a finding. With `none` or no key, report no such finding.
6. Report no finding whose failure case is an item of `## Out of scope` of the issue.
7. Report no finding whose failure needs an input or a state that does not exist today. A failure that can occur with a file that is in the repo today stays a finding. A failure that can occur with an input that the app accepts from outside the repo stays a finding (for example a server reply, a file that passes the schema, the input of a user).
8. Report no finding against a decision that the issue states. Rule 4 stays: an issue that asks for something false or impossible is a finding.
9. Report one finding for one cause. List in that finding each other place that the cause breaks.

## Writing

- Write all prose in ASD-STE100 Simplified Technical English. This includes docs, issues, ADRs, commit messages, skills, and `CLAUDE.md` / `AGENTS.md`. The `adhd-ste` output style holds the chat rules.
- For human docs, use the `humanize` skill for the doc rules. For a skill, `AGENTS.md` or `CLAUDE.md`, use the `writing-for-agents` skill. ASD-STE100 still applies to both.
- Change a file with the `Edit` or `Write` tool. Why: the harness file-state check sees only these two tools. A `python`, `sed -i` or heredoc write in Bash skips this check. This rule overrides the auto mode note that allows `sed`, heredoc and short-script edits.
- Code, identifiers, and quotations stay as they are.
- In code, scripts and config, write a comment as one line with one sentence, 160 characters or less from the comment marker. Two facts are 2 comments. Keep a comment only in one of these 4 classes:
  1. A `why:` comment for a fact about an external tool (git, zsh, Claude Code, an OS) that the code cannot show.
  2. A `why:` comment for a fact about our own design that the code cannot show, and that no test name or doc can hold.
  3. A script usage header, or the doc comment of a function that other code calls (inputs and result). It can have more lines.
  4. A line that a tool reads: a shebang, a lint suppression, a license line.

  Put a known shortcut in an issue.

## Git

- To commit or push, use the `ship` skill. Do not run `git commit` or `git push` yourself. A hook blocks them in the main session.
- Pass `ship` the paths you changed, a one-line summary, and the repo's message convention.
- When a change that the user asked for is done and its checks pass, call `ship`. Do not ask first. Ask only before you ship a file that the user did not ask to change.
- Do not add a `Co-Authored-By` line or other AI attribution to commits or PRs. The README states the AI use.
- The shell is zsh with `nonomatch`: an unmatched glob goes to the command as text. Quote a word that starts with `=`, or zsh stops with `= not found`.
- To wait for a long command, start it with `run_in_background`. To wait for a background command or agent, end the turn: the harness sends a notification. Do not call `sleep`. `pkill -f` and `pgrep -f` match their own shell.
- A commit subject names the change. It has no issue number: on a public repo, `#106` links to an unrelated GitHub issue, or to nothing.
- In a repo whose work folder is a symlink into another git repo, one `ship` call also commits and pushes the `<work folder>/...` paths that you pass, in that repo. For a change with no code paths, use `ship --issues` with the `<work folder>/...` paths.
- Default for a solo repo: one commit for each resolved issue, push to `main`, no PRs. A repo can override this.
