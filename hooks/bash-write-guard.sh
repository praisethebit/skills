#!/usr/bin/env bash
# PreToolUse (Bash): block a file write in Bash to a repo file. The agent uses the Edit or Write tool.
# why: the harness file-state check sees only Edit and Write
# why: the auto-mode prompt of the harness allows sed and heredoc writes, so the CLAUDE.md rule alone does not stop them
# why: the hook never stops a session on its own failure, so it exits 0
set -uo pipefail
command -v jq >/dev/null || exit 0
input=$(cat 2>/dev/null || true)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
[[ -n $cmd ]] || exit 0
deny() {
  echo "Change a repo file with the Edit or Write tool, not with $1 in Bash. Why: the harness file-state check sees only Edit and Write. A write to a path under /tmp passes." >&2
  exit 2
}
# why: a heredoc body and a quoted string are text, not a program, so a commit message or a Markdown quote passes the sed and redirect checks
# why: a quoted string right after `>` stays, because it is a redirect target
# why: the Python check reads the full command, because a Python program is a heredoc body
txt=$(awk '
  end != "" { if ($0 ~ "^[[:space:]]*" end "$") end = ""; next }
  match($0, /<<-?[[:space:]]*["\x27]?[A-Za-z_][A-Za-z_0-9]*/) {
    w = substr($0, RSTART, RLENGTH); gsub(/<<-?[[:space:]]*["\x27]?/, "", w); end = w
  }
  { print }' <<<"$cmd" | perl -0pe "s/(?<![>])(?<!> )(?<!tee )('[^']*'|\"(?:[^\"\\\\]|\\\\.)*\")/''/g")
# why: an in-place edit has no output path to test, so each one is a repo write
grep -qE '(^|[;&|(]|\s)(sed|perl)\s+(-[a-zA-Z]*i|--in-place)' <<<"$txt" && deny '`sed -i` or `perl -i`'
# why: a Python write names its path in a variable, so the hook tests for a /tmp path anywhere in the command.
if grep -qE "open\([^)]*,\s*['\"][wa]|\.write_text\(" <<<"$cmd" && ! grep -q '/tmp/' <<<"$cmd"; then
  deny 'a Python write'
fi
# why: a redirect or a tee to a file with a source or doc suffix is a repo write, unless the path is a temp path.
sfx='md|sh|json|jsonc|py|ts|tsx|js|go|kt|kts|yml|yaml|toml|txt|base|ps1|conf'
# why: a session sets S=<scratchpad> and writes to $S/x, so a variable set to a temp path is a temp path.
tmpvars=$(grep -oE '(^|[;&|[:space:]])[A-Za-z_][A-Za-z_0-9]*=["'"'"']?(/tmp/|\$TMPDIR|\$\{TMPDIR)' <<<"$cmd" | sed -E 's/^[;&|[:space:]]*//; s/=.*//')
# why: a relative write after `cd <temp dir>` is a temp write only when that cd is the one cd of the command.
cds=$(grep -oE '(^|[;&|(])[[:space:]]*cd[[:space:]]+[^;&|[:space:]]+' <<<"$txt" | sed -E 's/^.*cd[[:space:]]+//; s/["'"'"']//g')
tmpcwd=0
[[ -n $cds && $(grep -c . <<<"$cds") -eq 1 && $cds =~ ^(/tmp/|\$TMPDIR|\$\{TMPDIR) ]] && tmpcwd=1
while IFS= read -r t; do
  t=${t//[\"\']/}
  [[ $t == /tmp/* || $t == /dev/* || $t == '$TMPDIR'* || $t == '${TMPDIR'* ]] && continue
  for v in $tmpvars; do [[ $t == "\$$v/"* || $t == "\${$v}/"* ]] && continue 2; done
  [[ $tmpcwd == 1 && $t != /* && $t != '~'* && $t != '$'* ]] && continue
  [[ $t =~ \.($sfx)$ ]] && deny 'a shell redirect or `tee`'
done < <(
  grep -oE '(^|[^0-9&>])>>?\s*("[^"]*"|'"'[^']*'"'|[^[:space:];&|<>()]+)' <<<"$txt" | sed -E 's/^[^>]*>>?\s*//'
  grep -oE '(^|[[:space:]|])tee(\s+-a)?\s+("[^"]*"|'"'[^']*'"'|[^[:space:];&|<>()]+)' <<<"$txt" | sed -E 's/^.*tee(\s+-a)?\s+//'
)
exit 0
