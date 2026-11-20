# Audit finish: steps 6 and 7

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
