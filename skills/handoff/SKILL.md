---
name: handoff
description: Write a handoff file so a new Claude Code session in the same repo can continue the work. Only the user starts this skill, with /handoff.
argument-hint: "[focus]"
disable-model-invocation: true
---

Write a handoff file for the next agent. Focus (optional): $ARGUMENTS

The reader is a new Claude Code session on this machine, in this repo. It has this file and the repo, but not the conversation. Each step ends on its completion criterion.

1. **Check.** Run `git status --short --branch`, `git log --oneline -5` and `git log --oneline '@{upstream}..HEAD'`. The last command lists each commit that is not pushed. If it fails, the branch has no upstream: write that in State, and list the local commits. If the work folder is a symlink, also run `git -C "$(readlink -f <work folder>)" status --short --branch`, because the issue files are in that repo. Find the active issue of the session and read its frontmatter. If the session has no issue, write that in State. Done when you know the real state of the repo.
2. **Compare.** Compare the check with the conversation. Each disagreement (for example a change that the conversation does not mention) goes under Problems. Done when each disagreement has a line, or you found none.
3. **Write.** Get the time with `date +%Y%m%d-%H%M`. Get the repo root with `git -C <repo> rev-parse --show-toplevel`. `<repo>` is the repo of the session, also when the shell is in the work folder or in a different folder. If the command fails, the session has no repo: tell the user, write no file, and stop. Write `<root>/.handoffs/<YYYYMMDD-HHMM>.md`. Create the folder if it does not exist. If the file exists, add the suffix `-2` (then `-3`) to the name. Do not overwrite a file. Done when the file has the "Read first" line and these sections, in this order:
   - **Read first:** one line. It names the files and skills that the next agent must read.
   - **State:** where the work is now. Include each uncommitted change and each commit that is not pushed, also for the repo of a work folder symlink.
   - **Done:** what is finished.
   - **Decisions:** the decisions made, each with its reason.
   - **Pending decisions:** each open decision, with the name of the person who decides.
   - **Next:** start with the next action, as a command or a file path. If the user gave a focus, the aim of Next follows that text. If not, Next follows the plan of the conversation.
   - **Problems:** each open problem, with the exact error text.

   Rules: link to artifacts (files, issues, commits) and do not copy them. Redact secrets.
4. **Clean.** Delete the plain `*.md` files in `<root>/.handoffs/` that are older than 14 days: `find "<root>/.handoffs" -maxdepth 1 -type f -name '*.md' -mmin +20160 -delete`. Do not delete any other file. Done when the command ran.
5. **Print.** Print one line for the user to paste after `/clear`, for example `Read /abs/path/.handoffs/20261102-1430.md and continue the work.` Use the absolute path. Done when the line shows the real path.
