#!/usr/bin/env bash
# SessionStart hook: give a linked git worktree the work folder symlink of its main checkout, and copy the files that .worktreeinclude names.
# why: the work folder is gitignored, so `git worktree add` and `claude -w` do not copy it, and the skills read the issue files through it
# The hook never stops a session: each failure exits 0 with no change.
set -uo pipefail
input=$(cat 2>/dev/null || true)
dir=$(jq -r '.cwd // empty' <<<"$input" 2>/dev/null || true)
[[ -n $dir ]] || dir=$PWD
# why: on Windows the hook input has cwd as C:\..., and cygpath (in Git Bash) makes the form that the shell commands use
if command -v cygpath >/dev/null 2>&1; then dir=$(cygpath -u "$dir" 2>/dev/null || printf '%s' "$dir"); fi
top=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || exit 0
gitdir=$(git -C "$top" rev-parse --absolute-git-dir 2>/dev/null) || exit 0
common=$(git -C "$top" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || exit 0
# why: only a linked worktree has a git dir that is not the common git dir
[[ $gitdir != "$common" ]] || exit 0
main=$(dirname "$common")
# why: a new worktree has no gitignored file, for example local.properties with the Android SDK path
# why: .worktreeinclude in the main checkout names each file to copy, one path for each line, with no glob
if [[ -f $main/.worktreeinclude ]]; then
  while IFS= read -r f || [[ -n $f ]]; do
    f=${f%$'\r'}
    [[ -z $f || $f == '#'* || $f == /* || $f == *..* ]] && continue
    [[ -f $main/$f && ! -e $top/$f ]] && cp -p -- "$main/$f" "$top/$f" 2>/dev/null
  done <"$main/.worktreeinclude"
fi
wf=$(cd "$main" && bash "$(dirname "$(readlink -f "$0")")/../bin/work-folder" 2>/dev/null) || exit 0
if [[ ! -e $top/$wf && ! -L $top/$wf ]]; then
  [[ -L $main/$wf ]] || exit 0
  # why: an absolute target stays as it is, so the link is the same as in the main checkout
  target=$(readlink "$main/$wf") || exit 0
  [[ $target == /* ]] || target=$(readlink -f "$main/$wf") || exit 0
  mkdir -p "$(dirname "$top/$wf")" 2>/dev/null || true
  # why: in Git Bash, ln -s makes a copy unless MSYS has winsymlinks:nativestrict, and the session environment may not have it
  MSYS=winsymlinks:nativestrict ln -s "$target" "$top/$wf" 2>/dev/null || true
fi
[[ -L $top/$wf ]] || exit 0
real=$(readlink -f "$top/$wf") || exit 0
# why: the worktree guard refuses an Edit or a Write through the work folder link, and a Bash command that it cannot prove stays in the worktree
# shellcheck disable=SC2016
printf 'Worktree session. Read and edit the issue files at %s, not through %s: the worktree guard refuses an Edit or a Write through the link. Still give commit-push the %s/... paths. Write one plain command in each Bash call: the guard refuses a loop, a $variable in a sed, ssh or git argument, and a heredoc whose text has the word git. Edit a file with the Edit tool, not with a python or sed script.\n' "$real" "$wf" "$wf"
exit 0
