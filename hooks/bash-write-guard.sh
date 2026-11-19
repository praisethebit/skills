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
# why: a session sets S=<scratchpad> and writes to $S/x, so a variable set to a temp path is a temp path.
tmpvars=$(grep -oE '(^|[;&|[:space:]])[A-Za-z_][A-Za-z_0-9]*=["'"'"']?(/tmp/|\$TMPDIR|\$\{TMPDIR|\$\(mktemp|/mnt/[a-z]/Users/[^/]+/AppData/Local/Temp/)' <<<"$cmd" | sed -E 's/^[;&|[:space:]]*//; s/=.*//')
# why: a relative write after `cd <temp dir>` is a temp write only when that cd is the one cd of the command.
cds=$(grep -oE '(^|[;&|(])[[:space:]]*cd[[:space:]]+[^;&|[:space:]]+' <<<"$txt" | sed -E 's/^.*cd[[:space:]]+//; s/["'"'"']//g')
tmpcwd=0
if [[ -n $cds && $(grep -c . <<<"$cds") -eq 1 ]]; then
  [[ $cds =~ ^(/tmp/|\$TMPDIR|\$\{TMPDIR) ]] && tmpcwd=1
  for v in $tmpvars; do [[ $cds == "\$$v" || $cds == "\$$v/"* || $cds == "\${$v}"* ]] && tmpcwd=1; done
fi
# Return 0 when the write target $1 is a temp path: /tmp, /dev, TMPDIR, Windows Temp, a temp variable, or a relative path after a cd to /tmp.
is_tmp() {
  local t=${1//[\"\']/} v
  [[ $t == /tmp/* || $t == /dev/* || $t == '$TMPDIR'* || $t == '${TMPDIR'* || $t =~ ^/mnt/[a-z]/Users/[^/]+/AppData/Local/Temp/ ]] && return 0
  for v in $tmpvars; do [[ $t == "\$$v/"* || $t == "\${$v}/"* ]] && return 0; done
  [[ $tmpcwd == 1 && $t != /* && $t != '~'* && $t != '$'* ]] && return 0
  return 1
}
# why: the first word that is not an option is the sed or perl program, unless an -e or -f option gives it.
while IFS= read -r seg; do
  read -ra w <<<"$seg"
  prog=1 files=0
  for ((k = 1; k < ${#w[@]}; k++)); do
    x=${w[k]}
    case $x in
      -e | -f | --expression | --file) prog=0; ((k++)); continue ;;
      *'>'* | *'<'*) break ;;
      -*) continue ;;
    esac
    if ((prog)); then prog=0; continue; fi
    files=1
    is_tmp "$x" || deny '`sed -i` or `perl -i`'
  done
  ((files)) || deny '`sed -i` or `perl -i`'
done < <(grep -oE '(^|[;&|(]|\s)(sed|perl)\s+(-[a-zA-Z]*i|--in-place)[^;&|)]*' <<<"$txt" | sed -E 's/^[;&|([:space:]]+//')
# why: a Python write names its path in a literal or in a variable, so the hook tests the literal or the last string set to the variable.
if grep -qE "open\([^)]*,\s*['\"][wa]|\.write_text\(" <<<"$cmd"; then
  while IFS= read -r a; do
    a=$(sed -E 's/^\s+|\s+$//g' <<<"$a")
    if [[ $a =~ ^[\"\'](.*)[\"\']$ ]]; then
      val=${BASH_REMATCH[1]}
    elif [[ $a =~ ^[A-Za-z_][A-Za-z_0-9]*$ ]]; then
      val=$(grep -oE "(^|[^A-Za-z_0-9.])$a\s*=\s*[\"'][^\"']+[\"']" <<<"$cmd" | tail -1 | sed -E "s/^.*=\s*[\"']//; s/[\"']$//")
    else
      val=''
    fi
    if [[ -n $val ]]; then
      is_tmp "$val" || deny 'a Python write'
    elif ! grep -q '/tmp/' <<<"$cmd"; then
      deny 'a Python write'
    fi
  done < <(
    grep -oE "open\(\s*[^,)]+\s*,\s*['\"][wa]" <<<"$cmd" | sed -E "s/^open\(//; s/,\s*['\"][wa]$//"
    grep -oE "Path\(\s*[^)]+\)\.write_text\(" <<<"$cmd" | sed -E 's/^Path\(//; s/\)\.write_text\($//'
    grep -qE '\.write_text\(' <<<"$cmd" && ! grep -qE 'Path\([^)]+\)\.write_text\(' <<<"$cmd" && echo '?'
  )
fi
# why: a redirect or a tee to a file with a source or doc suffix is a repo write, unless the path is a temp path.
sfx='md|sh|json|jsonc|py|ts|tsx|js|go|kt|kts|yml|yaml|toml|txt|base|ps1|conf'
while IFS= read -r t; do
  is_tmp "$t" && continue
  [[ ${t//[\"\']/} =~ \.($sfx)$ ]] && deny 'a shell redirect or `tee`'
done < <(
  grep -oE '(^|[^0-9&>])>>?\s*("[^"]*"|'"'[^']*'"'|[^[:space:];&|<>()]+)' <<<"$txt" | sed -E 's/^[^>]*>>?\s*//'
  grep -oE '(^|[[:space:]|])tee(\s+-a)?\s+("[^"]*"|'"'[^']*'"'|[^[:space:];&|<>()]+)' <<<"$txt" | sed -E 's/^.*tee(\s+-a)?\s+//'
)
exit 0
