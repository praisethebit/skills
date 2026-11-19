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
3. **Match.** Look for an open issue that holds the same cause or the same seam as the request. Skip this step for "add idea: X". Done when you ran the match, and either asked the question, found no match, or appended to the issue that the request names.
   - An open issue is a file in `<work folder>/issues/` (not `done/`) with `status: open`, at any stage.
   - Grep the titles and bodies of the open issues for the file paths and the names of the skills, scripts and keys that the finding names. Read the `seam` key of each open issue for the seam test (rules below). Remove the excluded issues and the issues with a worktree (rules below) first. Then read a maximum of 3 candidates: a candidate from the seam test comes before a candidate from the grep, then the files with the most hits. This does not count against the cap of 8 code searches of the Look step.
   - A match is the same cause (the same failure from the same root), or the same seam: the finding and the issue share at least one file path, or name the same skill or script, or a file of the finding is in the seam of the issue.
   - **Seam test.** Write each path of the finding as a repo-relative path with no `:<line>` suffix, and add a missing `/` to a folder path. Then a file is in the seam of an issue when its path is equal to a file path of the `seam` key, or starts with a folder path of the `seam` key. A folder path ends with `/`, and the test compares the path with this `/`: a file in `app/ui2/` is not in the seam `app/ui/`. When the finding names a folder, the folder is in the seam when its path is equal to a folder path of the `seam` key, or starts with one. An issue with `seam: none` has no file in its seam. For an issue with a `seam` key, only the key decides: a file that the text of the issue names, and that is outside the seam, is outside.
   - Each issue number in the exclude list of the request is no match. The `/implement` skill passes the issue of its session in this list.
   - An open issue with a git worktree is no match. Why: `close-issue` would close the added finding with no work. Run `git worktree list` in the code repo, not in the folder that the work-folder symlink points to. A worktree of issue NNN is a line of `git worktree list` whose path ends in `/NNN` (`claude -w NNN` makes it). When `git worktree list` fails, write its error in the question text and continue.
   - On a match, ask one `AskUserQuestion`: one option "Add to issue NNN" for each matched candidate (a maximum of 3), each with the issue number, its title and a one-line reason for the match, so the user can see a false match (same file, different cause). Add the option "New issue". On "New issue", or with no match, continue with the Write step.
   - When the request names `append to NNN`, skip the grep and the question, and append to issue NNN.

   **Append** (on "Add to issue NNN"):
   - Count the `- [ ]` and `- [x]` lines under `## Acceptance criteria`. When the count after the append is a maximum of 10, and each file of the finding is in the seam of the issue, write the finding as one new criterion with its proof. The stage stays.
   - An issue with no `seam` key, or a finding that names no file and no folder: the count is the only test. Why: the user already picked "Add to issue NNN" or named `append to NNN`.
   - Otherwise (more than 10 criteria, a file outside the seam, a finding with files inside and outside the seam, or a finding that names a file or a folder for an issue with `seam: none`) add one bullet to an `## Added findings` section: `- <file>:<line>: <failure case> (source: <issue NNN, or "user request">)`. Put the section after `## Out of scope` and before `## Answer`. Set `stage: backlog`.
   - Then set `model` and `effort` of the open issue again: apply the rule in the tracker doc to the whole issue, with the new criterion or the added finding.
   - Skip the Write step: the number from `--claim` stays unused. Print one line `edited: <work folder>/issues/<file name>` with the path of the open issue. Ship that path in the Ship step.
   - One request can carry 2 or more findings. Count the criteria again after each append: when the count goes above 10, the finding goes to `## Added findings` and the stage moves to `backlog`.
4. **Write.** Write the issue in the tracker's format, with a maximum of 6 acceptance criteria. When the issue has acceptance criteria, end each criterion with its proof, for example `(proof: unit test)`, and add an `## Out of scope` section after the criteria ("None." is valid). An idea card needs neither. Set `stage` by the stage rule below. For "add idea: X", write the idea as the title and one line of text. When the search cap ends before you find all members of the class, write the missing members as an open question. When a review finding is the source, put the class and all known members in the issue. In a repo where the `AGENTS.md` has the line ``Behavior spec: `docs/spec/`.``, write a behavior criterion and `behavior_spec` (a file named after a durable capability of the product, not after this work) only when a criterion states what the product does (form: `## Behavior spec` in the tracker doc). With no behavior criterion, write no `behavior_spec` key. When the stage rule gives `next`, write `seam` from the files of the Look step (rules: `## Seam` in the tracker doc). Set `model` and `effort` with the rule in the tracker doc. Write each unknown as an open question. Done when the file exists.

   **Stage rule.** Use the first row that matches:

   | Case | `stage` |
   |---|---|
   | The user names the stage (`idea`, `backlog`, `spec` or `next`) | that stage |
   | The request is "add idea: X" | `idea` |
   | The issue has an open question, or a decision that only the user can make | `backlog` |
   | No open question, and the work needs more than 6 criteria or more than one seam | `spec` |
   | No open question, and a maximum of 6 criteria in one seam, each with its proof | `next` |

   For `spec`, write the decided facts in a `## Decisions` section: `/to-tickets` reads it. When you are not sure of the row, use `backlog`. Why: `/implement` stops on an issue that is not clear, and that stop costs one session.
5. **Ship.** If the work folder is a symlink, call `ship` with the `--issues` form and the `<work folder>/...` path of the issue file. Otherwise call `ship` with the issue file. The request to open the issue is also the request to commit. In an `/implement` session, stop after step 4 (after step 3 for an append): that session ships the file with its work. Done when the commit is pushed, or when the file waits for the `/implement` commit.
