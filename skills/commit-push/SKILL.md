---
name: commit-push
description: Commit and push changes. Use every time you commit or push in any repo. Pass the changed paths, a one-line summary, and the commit message convention.
---

Commit and push with the script `~/.claude/bin/ship`. Input:

$ARGUMENTS

1. Write the message:
   - The subject follows the repo convention. If there is no convention, copy the style of `git log -5 --format=%s`.
   - Add a body only for details. Write it in ASD-STE100 Simplified Technical English. Wrap at 72 characters.
   - The subject names the change. Do not put an issue number in the subject: on a public repo, `#106` links to an unrelated GitHub issue.
   - Do not add a `Co-Authored-By` line or other AI attribution. The README of each repo states the AI use.
2. From the repo root, run `~/.claude/bin/ship "<message>" -- <path>...` with only the changed paths. Set the Bash timeout to 600000: the hooks of a repo can take more than the default 2 minutes. For a path that you moved with `git mv` or removed with `git rm`, pass both the old path and the new path. The script stages and commits only those paths, pushes, and runs `git pull --rebase` one time if the remote is ahead.
3. If a pre-commit hook fails, fix the cause and run the script again. Never use `--no-verify`, `--force` or `git reset --hard`.
4. Tell the user the hash and subject. Tell the user about each file that the script lists as `not staged`.
5. The script exits 1 if a push fails. It prints `FAILED push of the code repo` or `FAILED push of the issue repo`. Tell the user which repo failed. A failed push in one repo does not undo the other.
6. If the script prints `pull --rebase failed`, fix the conflict with `git rebase`, then run the same script call again. With no new change in the paths, it only pushes.

Local extension: read `~/.claude/local/commit-push.md` when it exists, and follow its steps.

A repo whose work folder is a symlink into another git repo (the issue repo) keeps its issues there. Pass each issue file that you changed as a `<work folder>/...` path. The same call commits only those issue files in the issue repo, with the code repo name and hash in the body, and pushes both. All sessions share the issue repo, so the script does not commit the other changes there. For a file in `<work folder>/issues/done/`, it also commits the removal of the old path in `<work folder>/issues/`.

For a change with no code paths (for example a new issue), run `~/.claude/bin/ship --issues "<message>" -- <work folder path>...`. It commits and pushes only those issue files in the issue repo. It fails if the work folder is not a symlink into the issue repo. `ship --issues "<message>"` with no paths commits all changes in the issue repo. Use that form only when the user asks to commit all of them.

In a git worktree, the script pushes the branch to its upstream. If the branch has no upstream, the script sets it to the default branch of `origin`, so the commit goes to `main`.

To publish a tag, run `~/.claude/bin/ship --tag <name>`. Do this only when the user asks for a tag. The script tags the pushed `HEAD`, pushes only the tag, and makes no commit.
