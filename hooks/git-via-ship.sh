#!/bin/bash
# PreToolUse (Bash): block git commit/push in a Bash call of a session or a subagent.
input=$(cat)
# why: the ship script runs `git commit` in its own process, so the hook never sees that commit
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
# why: a heredoc body and a quoted string are text, not a program, so a script that edits `ship` or a grep for "git commit" passes
# why: keep the quotes of `bash -c "..."`, `eval` and `ssh`: they hold a command.
cmd=$(awk '
  end != "" { if ($0 ~ "^[[:space:]]*" end "$") end = ""; next }
  match($0, /<<-?[[:space:]]*["\x27]?[A-Za-z_][A-Za-z_0-9]*/) {
    w = substr($0, RSTART, RLENGTH); gsub(/<<-?[[:space:]]*["\x27]?/, "", w); end = w
  }
  { print }' <<<"$cmd")
if ! grep -qE '(^|[;&|(]|\s)(bash|sh|zsh|eval|ssh)\s' <<<"$cmd"; then
  cmd=$(perl -0pe "s/'[^']*'/''/g; s/\"(?:[^\"\\\\]|\\\\.)*\"/\"\"/g" <<<"$cmd")
fi
# why: a quote can start the command of `bash -c "..."` or `ssh host '...'`
git='(^|[;&|("'"'"']|\s)git(\s+-[cC]\s+\S+|\s+--[a-z-]+(=\S+)?)*'
seg='[^/\\[:space:]]+'
while IFS= read -r part; do
  grep -qE "$git\s+(commit|push)\b" <<<"$part" || continue
  # why: deleting a remote branch is not shipping, so the permission system decides
  grep -qE "$git\s+push\b.*(\s--delete\b|\s-d(\s|\$))" <<<"$part" && continue
  # why: a test repo in the session scratchpad is not a shipped repo
  # why: the hook cannot resolve a variable, so only one literal unquoted -C path right before commit or push counts
  # why: a ".." could leave the scratchpad
  # why: Windows has the scratchpad at %TEMP%\claude\<project>\<session>\scratchpad in 3 forms (/tmp, C:/ and C:\).
  # why: the drive letter and AppData\Local\Temp can have any case, so the C: forms match with grep -i.
  if ! grep -q '\.\.' <<<"$part" && {
    grep -qE "(^|\s)git\s+-C\s+/tmp/claude-[0-9]+/\S+/scratchpad/\S*\s+(commit|push)\b" <<<"$part" ||
      grep -qE "(^|\s)git\s+-C\s+/tmp/claude/$seg/$seg/scratchpad/\S*\s+(commit|push)\b" <<<"$part" ||
      grep -qiE "(^|\s)git\s+-C\s+[a-z]:[/\\\\]Users[/\\\\]$seg[/\\\\]AppData[/\\\\]Local[/\\\\]Temp[/\\\\]claude[/\\\\]$seg[/\\\\]$seg[/\\\\]scratchpad[/\\\\]\S*\s+(commit|push)\b" <<<"$part"
  }; then
    continue
  fi
  echo "Use the ship skill to commit or push. Pass it the changed paths, a summary and the message convention. For a test repo in the session scratchpad, use git -C <literal scratchpad path> commit." >&2
  exit 2
done < <(sed -E 's/(&&|\|\||[;&|])/\n/g' <<<"$cmd")
exit 0
