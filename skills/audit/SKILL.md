---
name: audit
description: One-shot quality audit of a repo or a folder. Finds bugs, security holes, scale problems, release risks, risky code without tests, slow paths, and code to delete, merge or split. Reports ranked findings, turns picked findings into issues, and changes no code.
disable-model-invocation: true
argument-hint: "[folder or package]"
---

## Opus guard

Do this check first, and again at the start of each turn until the skill ends. The skill ends after the `ship` call of the log, or when it writes no log (the user selects `stop`, or the work folder of the repo does not exist), or when the user picks no finding. Your system prompt names your model. If the model is not Opus and not Fable, stop. Do not do the next step. Tell the user: "This skill needs Opus or Fable. Press `s` in `/model`, pick Opus (the default) or Fable, then send your last message again."

Why: a `model:` key in a skill lasts for one turn only. Each reply of the user then goes back to the session model.

## Start

Audit $ARGUMENTS. When $ARGUMENTS is empty, audit the whole repo.

Audit like the senior developer who inherited this repo and gets the call when it breaks. The order of importance is: correct, safe, holds under load, can release and go back, tested, fast, lean. Lean is important: each extra line is a line that somebody must read, test and fix later. The user asked for this report, so give it in full.

## 0. Read the audit log

The audit log is the memory of past audits. One file for each audit: `<work folder>/audits/YYYY-MM-DD-HHMM.md`. Ticket labels are not reliable, so use the log and the code.

1. Read the newest file in `<work folder>/audits/`. If there is no file, go to step 1. Read a log in an older layout in the same way. A log with no `Scope:` line has the scope `whole repo`.
2. Open each logged finding, left-out entry and known entry at its path. Sort it: **gone** (the code no longer has the fault) or **still there**. A `Dropped` entry whose fault is gone is also gone: do not copy it to the new log.
3. Sort each finding that is still there:
   - **known**: its `#NNN` is an open issue (the issue file has `status: open`). For a finding with no number, an open issue in the issue folder has a title that names it.
   - **dropped**: the log has it under `Dropped`.
   - **open**: none of these.

   When `#NNN` is a closed issue and the fault is still there, report the fault as a new finding and name the closed issue.
4. Ask about each open finding that has no `asked` tag in the log. Use `AskUserQuestion` with a maximum of 4 findings in one call, and make as many calls as needed. Give each finding these options: `report it again` and 2 or 3 drop options. Write each drop option from the code of that finding, with the reason in the label (for example `drop: too small to merge`, `drop: differs on purpose`). The user can give a different drop reason in the text of "Other". If the text of "Other" says the user wants to keep the finding, treat it as `report it again`. The reason in the `Dropped` entry of the log is the text of the selected drop option without the `drop: ` prefix, or the text of "Other". Start no second dialog for the reason. A finding that the user wants again gets the tag `asked` in `Findings` of the new log, and you report it as a new finding. A finding with the tag `asked` is reported as a new finding and is not asked again.
5. Find the diff since the last audit. Read `Commit:` and `Scope:` of the newest log. Skip this sub-step when the scope of the log differs from the scope of this audit, or when the commit is not in the history. If not, run `git diff --stat <Commit>..HEAD -- <scope>`. For the scope `whole repo`, give no pathspec: run `git diff --stat <Commit>..HEAD`.
   - With 0 changed files, ask one question with `AskUserQuestion`: `continue with new probes` or `stop`. When the user selects `stop`, write no log and end the skill.
   - The report states one line after `What this repo does:`: "N files changed since the audit of <date>."
6. Put the logged `Not read` parts first in your reading plan. Put the changed files of the diff after them. Pick probes that differ from the logged `Probes`. The mutation probe of step 3 is an exception: run it again.

7. Count the entries of the old log: findings, left-out entries, known entries and `Dropped` entries. The sum of gone, known, dropped and reported again must equal that count. If not, find the entry that you did not sort, and sort it with sub-steps 2 to 4.

Done when each logged finding is gone, known, dropped, or reported again, the count check from sub-step 7 matches, and the diff rule has run.

## 1. Map the repo first

1. Read the README, the `AGENTS.md` / `CLAUDE.md`, the deploy and build config, the dependency list, the entry points (main, routes, handlers, jobs, CLI commands, scripts) and the tests.
2. Find the expected load: one person who runs a script, or many users and processes at the same time. Judge scale against that load. State the load that you assumed.
3. Trace the main flows from start to end: where data comes in, what the code stores, what goes out. Read these paths fully: user input, money, auth, data writes, background jobs, and all state that processes share.
4. Read `GLOSSARY.md` and `docs/adr/` when they exist. Use the glossary terms in finding titles.
5. Read approximately the last 100 commits (`git log --name-only -n 100 -- <the audited folder>`, or the whole repo when $ARGUMENTS is empty). Files that change often are hot spots.
6. In a big repo, go deep where a mistake costs the most. This is the first rule. The second rule is the change frequency: give more depth to hot spots. Do not read file by file. State the parts that you did not read.

## 2. Look for these problems

Skip a problem type that the repo has no surface for.

1. **Bug:** a wrong result, a crash, a missed edge case (empty, zero, last item, rounding, time zones). Callers that disagree with the return value of a function. The same rule with two different implementations.
2. **Risk:** security holes (injection, weak randomness, secrets in code, no check on user input). Data loss (swallowed errors, writes in the wrong order, no transaction). Untrusted text that reaches a prompt or a tool with privileges. A retry or a repeated delivery that does the work twice. A dependency with a known vulnerability: find it with the audit command of the package manager.
3. **Scale:** correct for one user, wrong for many. Check-then-write races, the same work in each process, memory or lists that only grow, one query for each item, O(n^2) on big input, per-process state that must be shared.
4. **Missing test:** risky logic (a branch, a parser, money, security, data writes) with no test that fails when the logic breaks. Ask for one good test, not for coverage.
5. **Speed:** big slowdowns are problems. Small gains (repeated work in a hot loop) are suggestions.
6. **Lean:** code that must not exist or must be smaller.
   - delete: dead code, unused options, flags and config, speculative features.
   - reuse: two helpers that do the same job. Keep one and name its path.
   - stdlib / native: the standard library or the platform already does it. A dependency that does what a few lines or the platform can do.
   - yagni: an interface with one implementation, a factory with one product, a wrapper that only passes calls through. Deletion test: "If you delete this, does the complexity collect in one place, or does it only move?" Report it only when it collects.
   - merge: near-copies that must change together. Name all repeated parts of the two copies in one finding. One concept that is spread over many small files is also a sign.
   - split: one function or class that does several unrelated jobs, so it is hard to read or test. Split by job. Never split by line count. Never make helpers only to make a function shorter.
7. **Operate:** applies only when the repo has a deploy or a release. The start from a clean checkout fails. Config fails late and not at the start. A data change (migration, backfill, import) has no way back. Logs leak secrets or personal data.

## 3. Probe the candidates

A probe is a check that shows that a suspected fault is real or not real. Limits:

- A probe runs on this machine only.
- A probe writes only in the scratchpad. It changes no repo file. The test command of the repo can write its usual build and cache files: this is allowed.
- A probe touches no live host, cluster, secret store or device. When only a live read can settle a Must fix candidate, ask the user first.
- The only network use is the audit command of the package manager.
- A probe that needs more than 2 minutes runs in the background.

Rules:

1. Run the test command of the repo one time, when it needs no device and no host. If not, the test run goes in `Not checked:`.
2. Each Must fix candidate gets one probe attempt. A candidate is a Must fix candidate when its impact meets the Must fix list of step 5.
3. A probe that shows no fault deletes the candidate. The probe stays in `Probes`.
4. A Must fix that stays `read` names what the probe needed, for example "needs an emulator".
5. Other findings get `read`, unless a run showed the fault. The tag never changes the group.
6. Mutation probe: when the `AGENTS.md` of the repo names a mutation command and the paths to skip, run that command in the background. Run it on the hand-written files that changed since the last audit (the diff of step 0.5) and on the hot spots (step 1.5). When step 0.5 did not run, use the hot spots only. Skip the paths that `AGENTS.md` names. With no such line in `AGENTS.md`, run no mutation probe.
   - The command can edit repo files and write build files. This rule overrides the limits above for that command only. After the run, run `git status` and restore each file that the run changed and that was clean before.
   - Sort a maximum of 50 survivors by the rules of step 4. Take the survivors in hot spots and in risky logic first. Put the count of the other survivors in `Not checked:` and in `Not read` of the log.
   - A survivor that passes step 4 is a "Missing test" finding with the tag `proven`.
   - When a permission denial stops the command, ask the user as the Blockers rule of `~/.claude/workflow.md` says. Do not drop the probe silently.
   - Step 3 is done only after the run ends and the survivors are sorted.

Each finding has one tag:

- `proven`: a run gave the wrong result, or a mutant that no test killed. A run is a test, a script or a command.
- `read`: the proof is a grep or a read of the code.

A grep stays a valid probe and goes in `Probes`, but it gives the tag `read`. A probe that shows that code works gives `proven` to no finding, also not to a different fault of the same code.

Done when each Must fix candidate has a probe result or a named need.

## 4. Check each finding before you report it

- Each finding needs a concrete case: "this input or situation gives this wrong result". No case, no finding. A missing item with no concrete case (for example "no health check") is not a finding.
- Before you call code unused, grep the full tree for it. Include tests, fixtures, config, and string or dynamic references.
- A shortcut is a decision, not a finding, only when an open issue (`status: open`) in the issue folder has a title that names it. In a repo with no issue folder, a shortcut is not a decision. Report such a shortcut only when the expected load is already past its limit.
- Propose the smallest fix that works. Prefer fixes that delete code. Do not add layers, frameworks or config that the problem does not need.
- Do not report style preferences, "consider" items, or vague worries.
- A decision in an ADR is a decision, not a finding. Report it only when it breaks the expected load, or when it causes a security hole or data loss. Then label it `contradicts ADR-NNNN`.
- A known fault is not a new finding. Each one goes in the `Known:` list. A dropped finding is not reported again and is not in the `Known:` list.

## 5. Output

Write in very simple English: short sentences and common words. Explain each technical term the first time you use it. The reader possibly never saw this code.

Start with `What this repo does:` in two or three sentences, and the load that you assumed. Add the diff line of step 0.5 when it ran.

Then give the findings in three groups, most important first. Skip empty groups.

The impact sets the group, not the type of problem. Normal use is what the owner or the users do on most days.

- **Must fix:** a security hole, data loss, a break at the expected load, a wrong result in normal use, a release that cannot start, or a data change with no way back.
- **Should fix:** a wrong result in a rare case, risky code without a test, real slowness, duplication, a function that mixes jobs, code that must not exist.
- **Nice to have:** small speed gains, shorter forms.

Number the findings across all groups, so that the user can say "fix 2 and 5". Give a maximum of 20 findings. Name each smaller finding that you left out in one line. Each finding has a title line with its tag, and all four parts, each part one or two short sentences. A Must fix with the tag `read` has one more line: `Probe needed: <what>`.

2. **Orders land on the wrong day** [proven] (`billing/close_day.py:L40-52`)
   - **What this is:** At midnight this job closes the day and bills all orders of that day.
   - **Problem:** It takes "today" from the server clock, which runs in UTC. A test run with a 00:30 Berlin order gave the day before.
   - **Fix:** Calculate the day one time in the time zone of the shop: `datetime.now(ZoneInfo("Europe/Berlin")).date()`. One line. Nothing else changes.
   - **If we skip it:** Late orders show the wrong date, and accounting must correct them by hand.

End with:

- `Known:` each known fault in one line, with its issue number or `no issue`.
- `Verdict:` one line. With a Must fix: what to fix first. With no Must fix: `Stop. No further audit until the next big change.`
- `Lean: -<N> lines, -<M> dependencies possible.` when lean findings exist.
- `Not checked:` the parts that you did not read or could not run.
- The question: "Which findings become issues?" The user answers with numbers in the chat.

When you find nothing: write `What this repo does:`, then `Healthy. Nothing to fix.`, and one line about what you checked.

## 6. Write the audit log

If the work folder of the repo exists, write `<work folder>/audits/YYYY-MM-DD-HHMM.md` with this fixed layout. A finding has its path and its symbol, not a line number. Why: line numbers move with each commit.

```
# Audit YYYY-MM-DD HH:MM

Commit: <short hash>
Scope: <folder, or `whole repo`>
Load: <the expected load>

## Findings
1. [proven] <title>: `<path>` (`<symbol>`). #NNN
2. [read, asked] <title>: `<path>` (`<symbol>`).

## Left out
- <title>: `<path>` (`<symbol>`).

## Known
- <title>: `<path>`. #NNN, or `no issue`

## Dropped
- <title>: `<path>` (`<symbol>`). Reason: <reason>. ADR candidate

## Probes
- <the check and its result>

## Not read
- <the part>
```

- `Probes`: a mutation run has one entry with the command, the run time and the counts of killed and survived mutants.
- `Dropped`: keep the old entries of the last log. Add the tag `ADR candidate` only when the reason meets the 3 ADR rules of `domain-modeling`: hard to reverse, surprising without context, and the result of a real trade-off. The user writes the ADR later. Do not write it.
- `#NNN` is the issue number. Step 7 adds it.

Done when each item in the report is in the log.

## 7. Turn findings into issues

1. Ask "Which findings become issues?" if the user did not answer yet. Wait for the numbers. With no findings, or when the user answers "none", go to sub-step 5.
2. Group the picked findings (skip sub-steps 2 to 4 when none are picked) by seam, with a maximum of 6 findings in one issue. Show the groups before you write.
3. Call `add-issue` one time for each group. Give it the 4 parts of each finding. `add-issue` sets the stage.
4. Write each `#NNN` in the log. Decide it for each group by itself: the `#NNN` of a group is the number of the issue that got the group.
   - `add-issue` made a new issue (it printed no `edited:` line): use the new number from `--claim`. This includes the user answer "New issue" in the match question.
   - `add-issue` appended the group to an open issue (it printed `edited: <work folder>/issues/<file name>`): use the digits before the first `-` of the file name, as written. Example: `042-some-title.md` gives `#042`. The number from `--claim` stays unused.
5. Ship the log as the last step: with `ship --issues` when the work folder is a symlink, with `ship` if not. `ship` commits only the `<work folder>/...` paths that it gets.

Done when the `ship` call of the log has run.

Do not change code. The skill writes only the log, the probe files in the scratchpad, and the issues through `add-issue`.
