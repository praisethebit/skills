#!/usr/bin/env python3
"""Collect Claude Code sessions and skills for the workflow review.

Reads only Claude Code logs (the session folder of each `--claude-home`,
default `~/.claude`). Keeps each entry whose `timestamp`
is in the review window. Emits:

  <out>/inventory.json        - skills, per-session stats
  <out>/transcripts/<id>.md   - one condensed transcript for each session

Everything runs locally; nothing is uploaded. Python 3.9+, stdlib only.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path, PureWindowsPath

DEFAULT_CLAUDE_HOMES = ("~/.claude",)
# why: the public-script grep check bans the plain folder name, so the name of the session folder is split
SESSION_DIR = "proj" "ects"
MAX_DIFF_LINES = 300
MAX_ARG_CHARS = 2000
OUTPUT_EDGE_LINES = 20  # why: only the first and last lines of a tool output stay, and an error stays full

CODE_EDIT_HINTS = ("apply_patch", "*** Begin Patch", "edit_file", "create_file", "str_replace", "write_file")
CLAUDE_CODE_EDIT_TOOLS = {"Edit", "MultiEdit", "NotebookEdit", "Write"}
DIFF_RESULT_TOOLS = {"Edit", "MultiEdit", "NotebookEdit"}
AGENT_TOOLS = {"Agent", "Task"}

GENERIC_TEST_PATTERNS = [
    r"\bpytest\b", r"\bpython3?\s+-m\s+(?:unittest|pytest)\b", r"\bgradlew?\b.*\b\w*[tT]est\w*\b",
    r"\b(?:npm|yarn|pnpm|bun)\s+(?:run\s+)?(?:test|check)\b", r"\badb\s+shell\s+am\s+instrument\b",
    r"\bcargo\s+(?:test|check)\b", r"\bgo\s+test\b", r"\bjest\b", r"\bvitest\b",
    r"\bplaywright\s+test\b", r"\bbats\b", r"\bmake\s+(?:test|check)\b", r"\bctest\b",
    r"\bmvn\b.*\btest\b", r"\btox\b", r"\bphpunit\b", r"\brspec\b",
]
FAIL_RE = re.compile(
    r"(?m)^(?:FAILED|FAIL\b|ERROR\b)|\b[1-9]\d*\s+(?:failed|failures?|errors?)\b"
    r"|Tests? failed|BUILD FAILED|AssertionError|Traceback \(most recent"
)
REDIRECT_RE = re.compile(r"(?:\d?>>?|\btee(?:\s+-a)?)\s*([^\s|;&>()]+)")
READ_VERB_RE = re.compile(r"\b(?:cat|tail|head|grep|rg|less|sed|awk|wc|bat)\b")
NON_TEST_COMMANDS = {"git", "ls", "cat", "head", "tail", "grep", "rg", "sed", "awk", "echo", "cd", "mkdir", "rm",
                    "cp", "mv", "pwd", "wc", "find", "true", "sleep", "jq", "printf", "export", "test", "["}
INTERPRETERS = {"bash", "sh", "zsh", "python", "python3", "node", "bun", "uv", "env"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist"}
WORK_FOLDER_RE = re.compile(r"^Work folder: `([^`]+)`\.$", re.M)


def work_folder(repo):
    """Work folder name of a repo: the `Work folder:` line of its AGENTS.md, else `planning`."""
    try:
        text = (Path(repo) / "AGENTS.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "planning"
    m = WORK_FOLDER_RE.search(text)
    if not m:
        return "planning"
    value = m.group(1).rstrip("/")
    if value.startswith("./"):
        value = value[2:]
    if not value or value.startswith("/") or ".." in value.split("/"):
        print(f"error: bad work folder `{m.group(1)}` in {Path(repo) / 'AGENTS.md'}", file=sys.stderr)
        sys.exit(1)
    return value


def parse_window(value):
    """Return (start, end) as aware UTC datetimes.

    "" = today from local midnight; Nh = last N hours; Nd = last N days;
    YYYY-MM-DD = that local day, midnight to midnight.
    """
    value = (value or "").strip()
    now = datetime.now().astimezone()
    if not value:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif re.fullmatch(r"\d+h", value):
        start, end = now - timedelta(hours=int(value[:-1])), now
    elif re.fullmatch(r"\d+d", value):
        start, end = now - timedelta(days=int(value[:-1])), now
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            day = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise SystemExit(f"error: invalid date '{value}'")
        start = day.astimezone()
        end = (day + timedelta(days=1)).astimezone()
    else:
        raise SystemExit(f"error: invalid window '{value}' (use empty, Nh, Nd or YYYY-MM-DD)")
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def parse_ts(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


REVIEW_COMMAND_TAG = "<command-name>/workflow-review</command-name>"


def has_review_command(path: Path) -> bool:
    """True if any user message of the session holds the /workflow-review command tag.

    why: a review session must not score itself. The session can start with /clear
    or /model, so the check covers all user messages, not only the first.
    """
    try:
        for obj in iter_jsonl_records(path):
            message = obj.get("message")
            if obj.get("type") != "user" or not isinstance(message, dict):
                continue
            if REVIEW_COMMAND_TAG in extract_text(message.get("content")):
                return True
    except OSError:
        return False
    return False


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--since",
        default="",
        help="window start as an ISO 8601 UTC time; the window ends now (cannot combine with --window)",
    )
    p.add_argument(
        "--window",
        default="",
        help="review window: empty (today from local midnight), Nh, Nd or YYYY-MM-DD",
    )
    p.add_argument(
        "--claude-home",
        action="append",
        default=[],
        help="Claude Code config directory (repeatable; default: ~/.claude)",
    )
    p.add_argument(
        "--repo",
        action="append",
        default=[],
        help="project to include (repeatable; default: git root of cwd, else cwd)",
    )
    p.add_argument(
        "--all-sessions",
        action="store_true",
        help="collect sessions from every project (cannot combine with --repo)",
    )
    p.add_argument("--skills-dir", action="append", default=[], help="extra skills directory to scan (repeatable)")
    p.add_argument(
        "--test-pattern",
        action="append",
        default=[],
        help="extra regex that marks a Bash command as a test run (repeatable; from the repo AGENTS.md)",
    )
    p.add_argument(
        "--include-headless",
        action="store_true",
        help="also collect headless claude -p sessions (entrypoint sdk-cli); the default skips them",
    )
    p.add_argument("--out", default="./workflow-review-run")
    return p.parse_args()


def resolve_repo(repo_arg) -> Path:
    if repo_arg:
        return Path(repo_arg).expanduser().resolve()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0 and res.stdout.strip():
            return Path(res.stdout.strip()).resolve()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return Path.cwd().resolve()


def resolve_repos(repo_args):
    if not repo_args:
        return [resolve_repo(None)]
    repos = []
    seen = set()
    for value in repo_args:
        repo = resolve_repo(value)
        if repo in seen:
            continue
        seen.add(repo)
        repos.append(repo)
    return repos


def discover_skills(repos, claude_homes, extra_dirs):
    """Global, repo and plugin skills. Always all three."""
    if isinstance(repos, Path):
        repos = [repos]
    roots = []
    for repo in repos:
        roots.extend((repo / ".agents" / "skills", repo / ".claude" / "skills"))
    roots.append(Path.home() / ".agents" / "skills")
    for home in claude_homes:
        roots.append(home / "skills")
    roots += [Path(d).expanduser() for d in extra_dirs]
    plugin_skill_files = []
    for home in claude_homes:
        plugins = home / "plugins"
        if plugins.is_dir():
            plugin_skill_files.extend(
                f for f in sorted(plugins.glob("**/skills/*/SKILL.md"))
                if ".trash" not in f.parts
            )

    candidates = []
    for root in roots:
        if root.is_dir():
            candidates.extend(sorted(root.glob("*/SKILL.md")))
    candidates.extend(plugin_skill_files)

    skills = {}
    for skill_md in candidates:
        name = skill_md.parent.name
        if name in skills:
            continue
        try:
            text = skill_md.read_text(errors="replace")
            stat = skill_md.stat()
        except OSError:
            continue
        desc = ""
        m = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
        if m:
            desc = m.group(1).strip().strip("\"'")[:300]
        skills[name] = {
            "name": name,
            "path": str(skill_md),
            "description": desc,
            "bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }
    return skills


def find_claude_session_files(claude_homes, start: datetime):
    """Find Claude Code session files that can hold an entry at or after `start`.

    The file mtime is only a cheap pre-filter: a file last written before
    `start` has no entry in the window. The entry timestamps decide.
    Subagent logs are not sessions: the parent session inlines them.
    """
    files = []
    for claude_home in claude_homes:
        session_dir = claude_home / SESSION_DIR
        if not session_dir.is_dir():
            continue
        for path in session_dir.glob("*/*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if mtime >= start:
                files.append((mtime, path))
    files.sort(key=lambda item: item[0], reverse=True)
    return files


def truncate(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f" …[truncated {len(text) - limit} chars]"


def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                t = block.get("text") or block.get("content") or ""
                if isinstance(t, str) and t:
                    parts.append(t)
            elif isinstance(block, str):
                parts.append(block)
    return "\n".join(parts)


def iter_jsonl_records(path: Path):
    """Yield every valid JSON object without loading the whole file."""
    stream = path.open("r", encoding="utf-8", errors="replace")

    def records():
        with stream:
            for line in stream:
                try:
                    yield json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

    return records()


def detect_skill_candidates(text: str):
    """Extract possible installed-skill names from one tool argument payload."""
    normalized = text.replace("\\", "/")
    candidates = set(re.findall(r"(?:^|/)skills/+([^/]+)/+", normalized))
    candidates.update(re.findall(
        r'"(?:skill|name|bundled_skill_id)"\s*:\s*"([^"]+)"',
        normalized,
    ))
    return candidates

def clip_lines(text: str, limit: int) -> str:
    lines = text.split("\n")
    if len(lines) <= limit:
        return text
    return "\n".join(lines[:limit]) + f"\n…[truncated {len(lines) - limit} lines]"


# why: the Outcome scorer must see every acceptance criterion, and a long issue file loses its criteria in the omitted middle lines
ISSUE_PATH_RE = re.compile(r"(?:^|/)issues/(?:done/)?\d+-[^/]+\.md$")


def is_issue_path(path: str) -> bool:
    return bool(ISSUE_PATH_RE.search(path.replace("\\", "/")))


# why: a Bash read of one issue file must keep all acceptance criteria, as a Read does
# why: a file name that starts with "*" (all issues) stays cut
ISSUE_READ_VERBS = {"cat", "head", "tail", "sed", "bat", "less"}
ISSUE_FILE_RE = re.compile(r"(?:^|[\s/])issues/(?:done/)?\d+-[^\s/]*\.md\b")


def is_issue_read_command(cmd: str) -> bool:
    for seg in command_segments(cmd.replace("\\", "/")):
        words = seg.split()
        if words and words[0] in ISSUE_READ_VERBS and ISSUE_FILE_RE.search(seg):
            return True
    return False


def clip_output(text: str, is_error: bool, keep_full: bool = False) -> str:
    text = text.strip()
    if is_error or keep_full:
        return text
    lines = text.split("\n")
    if len(lines) <= 2 * OUTPUT_EDGE_LINES:
        return text
    omitted = len(lines) - 2 * OUTPUT_EDGE_LINES
    return "\n".join(lines[:OUTPUT_EDGE_LINES] + [f"…[{omitted} lines omitted]"] + lines[-OUTPUT_EDGE_LINES:])


def format_patch(patch) -> str:
    """Render a Claude Code `structuredPatch` as unified-diff text."""
    out = []
    for hunk in patch or []:
        if not isinstance(hunk, dict):
            continue
        out.append(
            f"@@ -{hunk.get('oldStart')},{hunk.get('oldLines')} +{hunk.get('newStart')},{hunk.get('newLines')} @@"
        )
        out.extend(str(x) for x in hunk.get("lines") or [])
    return "\n".join(out)


WRAPPER_RE = re.compile(r"^(?:\w+=\S*\s+|time\s+|timeout\s+\S+\s+|sudo\s+|nohup\s+|uv\s+run\s+|(?:\S*/)(?=\S))*")


def command_segments(cmd: str, wrap=True):
    """Split a shell command into segments. Drop heredoc bodies and quoted text."""
    cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?(?:\n\1\b|\Z)", " ", cmd, flags=re.S)
    cmd = re.sub(r"'[^']*'|\"[^\"]*\"", "''", cmd)
    out = []
    for seg in re.split(r"&&|\|\||[;|\n(){}]", cmd):
        seg = seg.strip()
        if seg.startswith("cd ") or not seg:
            continue
        out.append(WRAPPER_RE.sub("", seg, count=1) if wrap else seg)
    return out


def discover_test_scripts(repos):
    """Repo scripts with `test` or `check` in the file name (depth <= 3)."""
    found = set()
    for repo in repos:
        if not repo.is_dir():
            continue
        base_depth = len(repo.parts)
        skip_path = Path(repo) / work_folder(repo)
        for root, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and Path(root) / d != skip_path]
            if len(Path(root).parts) - base_depth >= 3:
                dirs[:] = []
            for name in files:
                if re.search(r"test|check", name, re.I) and Path(name).suffix in {".sh", ".py", ".js", ".mjs", ".ts", ""}:
                    found.add(name)
    return found


class SessionParser:
    """Parse one session file, plus the subagent logs it started, into entries.

    An entry is (role, text). A subagent entry has the prefix "sub:" once for
    each depth level. A test run adds a ("test", ...) mark after its output.
    """

    def __init__(self, main_path, start, end, test_matchers, scripts_for_cwd, user_matchers=()):
        self.main_path = main_path
        self.start, self.end = start, end
        self.test_matchers = test_matchers
        self.user_matchers = user_matchers
        self.scripts_for_cwd = scripts_for_cwd
        self.test_scripts = set()
        self.entries = []
        self.stats = {
            "user_turns": 0, "assistant_turns": 0, "tool_calls": 0,
            "repeated_tool_calls": 0, "error_outputs": 0, "test_runs": 0, "subagents": 0,
        }
        self.meta = {}
        self.skills_used = set()
        self.used_tool_names = set()
        self.has_code_edit_hint = False
        self.first_ts = self.last_ts = None
        self.headless = False
        self.subagent_files = {}
        self.full_read_ids = set()
        sub_dir = main_path.with_suffix("") / "subagents"
        if sub_dir.is_dir():
            for meta_file in sub_dir.glob("*.meta.json"):
                try:
                    tool_use_id = json.loads(meta_file.read_text()).get("toolUseId")
                except (OSError, ValueError):
                    continue
                log = meta_file.with_name(meta_file.name[: -len(".meta.json")] + ".jsonl")
                if tool_use_id and log.is_file():
                    self.subagent_files[tool_use_id] = log
        self._visited = set()
        self._scripts_ready = False

    def emit(self, depth, role, text):
        self.entries.append(("sub:" * depth + role, text))

    def is_test_command(self, cmd, skill_span):
        """Return the detection reason, or None. Looks only at the start of each command segment."""
        segments = command_segments(cmd)
        if skill_span and any(seg.split()[0] not in NON_TEST_COMMANDS for seg in segments if seg.split()):
            return f"skill {skill_span}"
        for seg in command_segments(cmd, wrap=False):
            for pattern in self.user_matchers:
                if pattern.search(seg):
                    return f"pattern {pattern.pattern}"
        for seg in segments:
            for pattern in self.test_matchers:
                if pattern.match(seg):
                    return f"pattern {pattern.pattern}"
            toks = [t for t in re.split(r"\s*\d?>>?\s*\S+", seg)[0].split()]
            if toks and toks[0].rsplit("/", 1)[-1] in INTERPRETERS:
                toks = [t for t in toks[1:] if not t.startswith("-")]
            head = toks[0].rsplit("/", 1)[-1] if toks else ""
            if head in self.test_scripts:
                return f"script {head}"
        return None

    def run(self):
        self.parse_file(self.main_path, 0)
        # why: a subagent log with no toolUseId in its meta file (forked skill, nested agent) has no Agent call to sit below, so it goes at the end of the parent
        sub_dir = self.main_path.with_suffix("") / "subagents"
        if sub_dir.is_dir():
            for log in sorted(sub_dir.glob("*.jsonl")):
                if log not in self._visited:
                    self.stats["subagents"] += 1
                    self.emit(1, "note", f"[subagent log with no Agent call link: {log.name}]")
                    self.parse_file(log, 1)
        return self.first_ts is not None

    def parse_file(self, path, depth):
        if path in self._visited:
            return
        self._visited.add(path)
        try:
            records = iter_jsonl_records(path)
        except OSError:
            return
        seen_calls = {}
        seen_assistant = set()
        tool_names = {}
        pending_tests = {}
        held_marks = {}
        read_joins = {}
        skill_span = None

        for obj in records:
            ts = obj.get("timestamp")
            ts_dt = parse_ts(ts)
            in_window = ts_dt is not None and start_le(self.start, ts_dt, self.end)
            if depth == 0:
                if in_window:
                    self.first_ts = self.first_ts or ts
                    self.last_ts = ts
                if not self.meta and obj.get("sessionId"):
                    self.meta = {
                        "id": obj.get("sessionId"), "cwd": obj.get("cwd"), "started_at": ts,
                        "originator": "claude-code", "thread_source": None,
                        "cli_version": obj.get("version"), "entrypoint": obj.get("entrypoint"),
                    }
                elif self.meta:
                    self.meta["cwd"] = self.meta.get("cwd") or obj.get("cwd")
                    self.meta["started_at"] = self.meta.get("started_at") or ts
                    self.meta["cli_version"] = self.meta.get("cli_version") or obj.get("version")
                    self.meta["entrypoint"] = self.meta.get("entrypoint") or obj.get("entrypoint")
                if self.meta.get("cwd") and not self._scripts_ready:
                    self._scripts_ready = True
                    self.test_scripts = self.scripts_for_cwd(self.meta["cwd"])
                if self.meta.get("entrypoint") == "sdk-cli":
                    self.headless = True
            if not in_window:
                continue
            record_type = obj.get("type")
            message = obj.get("message")
            if record_type not in ("user", "assistant") or not isinstance(message, dict):
                continue

            role = message.get("role") or record_type
            content = message.get("content")
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
            has_user_text = False

            if role == "assistant" and depth == 0:
                message_id = message.get("id") or obj.get("uuid")
                if message_id and message_id not in seen_assistant:
                    seen_assistant.add(message_id)
                    self.stats["assistant_turns"] += 1

            tool_result_extra = obj.get("toolUseResult")
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "text":
                    text = block.get("text")
                    if not isinstance(text, str) or not text or looks_injected(text):
                        continue
                    if role == "user" and obj.get("isMeta"):
                        continue  # why: Claude Code injects the skill body after a Skill call
                    if role == "user":
                        has_user_text = True
                        skill_span = None
                        self.emit(depth, "user", text.strip())
                    elif role == "assistant":
                        self.emit(depth, "assistant", text.strip())
                elif block_type == "tool_use":
                    skill_span = self.on_tool_use(block, ts_dt, depth, seen_calls, tool_names,
                                                  pending_tests, held_marks, read_joins, skill_span)
                elif block_type == "tool_result":
                    self.on_tool_result(block, ts_dt, depth, tool_result_extra, tool_names,
                                        pending_tests, held_marks, read_joins)
            if role == "user" and has_user_text and depth == 0:
                self.stats["user_turns"] += 1

        for mark in held_marks.values():
            self.emit_mark(depth, mark, joined=False)

    def on_tool_use(self, block, ts_dt, depth, seen_calls, tool_names, pending_tests, held_marks, read_joins, skill_span):
        self.stats["tool_calls"] += 1
        name = str(block.get("name") or "unknown")
        tool_id = block.get("id")
        args = block.get("input") or {}
        args_text = args if isinstance(args, str) else json.dumps(args, ensure_ascii=False)
        key = hashlib.sha1((name + args_text).encode()).hexdigest()
        seen_calls[key] = seen_calls.get(key, 0) + 1
        if seen_calls[key] > 1:
            self.stats["repeated_tool_calls"] += 1
        self.used_tool_names.add(name)
        self.skills_used.update(detect_skill_candidates(args_text))
        self.has_code_edit_hint = self.has_code_edit_hint or any(h in args_text for h in CODE_EDIT_HINTS)
        if tool_id:
            tool_names[tool_id] = name
        is_dict = isinstance(args, dict)

        if name == "Skill" and is_dict and args.get("skill"):
            self.skills_used.add(args["skill"])
            skill_span = args["skill"] if re.search(r"test|check", str(args["skill"]), re.I) else None

        if name == "Write" and is_dict:
            body = clip_lines(str(args.get("content") or ""), MAX_DIFF_LINES)
            self.emit(depth, f"tool:{name}", truncate(json.dumps({"file_path": args.get("file_path")}), MAX_ARG_CHARS))
            self.emit(depth, "diff", f"[Write {args.get('file_path')}]\n{body}")
        elif name in DIFF_RESULT_TOOLS and is_dict:
            drop = ("old_string", "new_string", "edits") if name != "NotebookEdit" else ()
            short = {k: v for k, v in args.items() if k not in drop}
            self.emit(depth, f"tool:{name}", truncate(json.dumps(short, ensure_ascii=False), MAX_ARG_CHARS))
        else:
            self.emit(depth, f"tool:{name}", truncate(args_text, MAX_ARG_CHARS))

        if name == "Bash" and is_dict:
            cmd = str(args.get("command") or "")
            if tool_id and is_issue_read_command(cmd):
                self.full_read_ids.add(tool_id)
            joined_key = None
            if READ_VERB_RE.search(cmd):
                joined_key = next((k for k in held_marks if len(k) > 3 and k in cmd), None)
            reason = None if joined_key else self.is_test_command(cmd, skill_span)
            if joined_key:
                read_joins[tool_id] = joined_key
            elif reason:
                info = {"cmd": cmd, "reason": reason, "start": ts_dt, "result": None, "file": None,
                        "background": bool(args.get("run_in_background"))}
                redirect = REDIRECT_RE.findall(re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?(?:\n\1\b|\Z)", " ", cmd, flags=re.S))
                redirect = [f for f in redirect if f not in ("/dev/null", "/dev/stderr", "/dev/stdout")]
                if redirect:
                    info["file"] = redirect[-1]
                pending_tests[tool_id] = info
        elif name in ("Read", "TaskOutput", "BashOutput") and is_dict:
            if name == "Read" and tool_id and is_issue_path(str(args.get("file_path") or "")):
                self.full_read_ids.add(tool_id)
            target = str(args.get("file_path") or args.get("task_id") or args.get("bash_id") or "")
            for key in held_marks:
                if target and len(key) > 3 and (key in target or target.endswith(key.lstrip("./"))):
                    read_joins[tool_id] = key
        elif name in AGENT_TOOLS and tool_id in self.subagent_files:
            self.stats["subagents"] += 1
            self.parse_file(self.subagent_files[tool_id], depth + 1)
        return skill_span

    def on_tool_result(self, block, ts_dt, depth, extra, tool_names, pending_tests, held_marks, read_joins):
        result = extract_text(block.get("content"))
        is_error = bool(block.get("is_error"))
        low = result[:2000].lower()
        if is_error or "error" in low or "failed" in low or "traceback" in low:
            self.stats["error_outputs"] += 1
        tool_id = block.get("tool_use_id")
        self.emit(depth, "output", clip_output(result, is_error, tool_id in self.full_read_ids))
        if tool_names.get(tool_id) in DIFF_RESULT_TOOLS and isinstance(extra, dict):
            diff = format_patch(extra.get("structuredPatch"))
            if diff:
                self.emit(depth, "diff", f"[Edit {extra.get('filePath')}]\n{clip_lines(diff, MAX_DIFF_LINES)}")
        passed = not (is_error or FAIL_RE.search(result))
        if tool_id in read_joins:
            passed = not FAIL_RE.search(result)  # why: a grep with no match exits 1, and that is not a test failure
        if tool_id in pending_tests:
            info = pending_tests.pop(tool_id)
            info.update(passed=passed, end=ts_dt)
            key = info["file"]
            if info.get("background") and isinstance(extra, dict) and extra.get("backgroundTaskId"):
                key = str(extra["backgroundTaskId"])
            if key:
                if key in held_marks:
                    self.emit_mark(depth, held_marks[key], joined=False)
                held_marks[key] = info
            else:
                self.emit_mark(depth, info)
        elif tool_id in read_joins:
            info = held_marks.pop(read_joins.pop(tool_id), None)
            if info:
                # why: the read output holds the real result of the test run
                info.update(passed=passed, end=ts_dt)
                self.emit_mark(depth, info, joined=True)

    def emit_mark(self, depth, info, joined=None):
        self.stats["test_runs"] += 1
        dur = ""
        if info.get("start") and info.get("end"):
            dur = f" | {(info['end'] - info['start']).total_seconds():.1f}s"
        verdict = "PASS" if info.get("passed") else "FAIL"
        note = " (output file never read: result is from the launch)" if joined is False else ""
        cmd = " ".join(info["cmd"].split())
        self.emit(depth, "test", f"{truncate(cmd, 300)} | {verdict}{dur} | detected by {info['reason']}{note}")


def start_le(start, ts_dt, end):
    return start <= ts_dt < end


def parse_claude_session(path: Path, start, end, test_matchers, scripts_for_cwd, user_matchers=()):
    """Normalize one Claude Code JSONL session (and its subagents) to a transcript."""
    parser = SessionParser(path, start, end, test_matchers, scripts_for_cwd, user_matchers)
    if not parser.run():
        return None
    meta, stats = parser.meta, parser.stats
    if not meta:
        meta = {"id": path.stem, "cwd": None, "started_at": parser.first_ts,
                "originator": "claude-code", "thread_source": None}
    meta["headless"] = parser.headless
    stats["first_ts"] = parser.first_ts
    stats["last_ts"] = parser.last_ts
    stats["has_code_edits"] = bool(parser.used_tool_names & CLAUDE_CODE_EDIT_TOOLS) or parser.has_code_edit_hint
    return meta, stats, parser.entries, sorted(parser.skills_used)


def looks_injected(text: str) -> bool:
    head = text.lstrip()[:80]
    return head.startswith("<") and any(
        tag in head
        for tag in (
            "environment_context", "user_instructions", "ENVIRONMENT", "system-reminder",
            "permissions", "collaboration_mode", "recommended_plugins", "turn_context",
            "user_info",
        )
    )


def session_repo(cwd, repos):
    """Git root of a session cwd, else the matching repo in scope."""
    if cwd:
        path = Path(cwd).expanduser()
        if path.is_dir():
            try:
                res = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                                     capture_output=True, text=True, timeout=10)
                if res.returncode == 0 and res.stdout.strip():
                    return Path(res.stdout.strip()).resolve()
            except (subprocess.TimeoutExpired, OSError):
                pass
    for repo in repos:
        if session_matches_repo(cwd, repo):
            return repo
    return None


_git_cache = {}


def git_log_patch(repo, first_ts, last_ts):
    """`git log -p` for one repo between two timestamps."""
    key = (repo, first_ts, last_ts)
    if key not in _git_cache:
        try:
            res = subprocess.run(
                ["git", "-C", str(repo), "log", "-p", "--all", "--no-color", f"--since={first_ts}", f"--until={last_ts}"],
                capture_output=True, text=True, timeout=60, errors="replace",
            )
            _git_cache[key] = res.stdout.strip() if res.returncode == 0 else f"(git log failed: {res.stderr.strip()})"
        except (subprocess.TimeoutExpired, OSError) as exc:
            _git_cache[key] = f"(git log failed: {exc})"
    return _git_cache[key]


def render_transcript(meta, stats, skills_used, entries, git_logs=None) -> str:
    lines = [
        f"# Session {meta.get('id')}" + (" [headless]" if meta.get("headless") else ""),
        f"- cwd: {meta.get('cwd')}",
        f"- started: {meta.get('started_at') or stats.get('first_ts')}",
        f"- headless: {'yes (entrypoint sdk-cli)' if meta.get('headless') else 'no'}",
        f"- skills detected: {', '.join(skills_used) or '(none)'}",
        f"- stats: {stats['user_turns']} user turns, {stats['assistant_turns']} assistant turns, "
        f"{stats['tool_calls']} tool calls ({stats['repeated_tool_calls']} repeated), "
        f"{stats['error_outputs']} error-ish outputs, {stats['test_runs']} test runs, "
        f"{stats['subagents']} subagents, code edits: {stats['has_code_edits']}",
        "",
        "## Transcript",
        "",
    ]
    for role, text in entries:
        depth = role.count("sub:")
        base = role.replace("sub:", "")
        label = f"{'  ' * depth}[{'subagent ' * (1 if depth else 0)}{base}]"
        first, *rest = text.split("\n")
        lines.append(f"{label} {first}")
        lines.extend(("  " * depth) + "  " + r for r in rest)
        lines.append("")
    lines += ["## Git log (window of this session)", ""]
    if git_logs:
        for repo, git_log in git_logs:
            lines += [f"Repo: {repo}", "", "```diff", git_log or "(no commit in the window)", "```", ""]
    else:
        lines.append("(no commit in the window, or no repo found)")
    return "\n".join(lines) + "\n"


def session_matches_repo(cwd, repo: Path) -> bool:
    """True when a session's recorded cwd belongs to this repo.

    Two ways to match:
    1. cwd is inside the repo root (same-machine sessions).
    2. cwd's trailing directory name equals the repo's name (git
       worktrees like <dir>/<id>/<repo-name>, and Windows sessions).
    Basename matching can over-match if two different repos share a
    directory name; acceptable for a report.
    """
    if not cwd:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", cwd) or "\\" in cwd:
        # why: a PosixPath of a Windows cwd would be relative to the script cwd
        return PureWindowsPath(cwd).name == repo.name
    p = Path(cwd)
    try:
        if p.resolve().is_relative_to(repo):
            return True
    except OSError:
        pass  # why: a cwd from another machine may not exist locally
    return p.name == repo.name


def session_matches_repos(cwd, repos) -> bool:
    return any(session_matches_repo(cwd, repo) for repo in repos)


def infer_session_repos(sessions):
    repos = []
    seen = set()
    for session in sessions:
        cwd = session["meta"].get("cwd")
        if not cwd:
            continue
        path = Path(cwd).expanduser()
        if not path.is_dir():
            continue
        try:
            result = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        if result.returncode != 0 or not result.stdout.strip():
            continue
        repo = Path(result.stdout.strip()).resolve()
        if repo in seen:
            continue
        seen.add(repo)
        repos.append(repo)
    return repos


def detect_skills_from_entries(entries, skill_names):
    tool_text = "\n".join(
        text
        for role, text in entries
        if role.replace("sub:", "") == "skill" or role.replace("sub:", "").startswith("tool:")
    ).replace("\\", "/")
    detected = set()
    for name in skill_names:
        markers = (
            f"skills/{name}/",
            f"{name}/SKILL.md",
            f'"skill": "{name}"',
            f'"name": "{name}"',
            f'"bundled_skill_id": "{name}"',
        )
        if any(marker in tool_text for marker in markers):
            detected.add(name)
    return detected


def main():
    args = parse_args()
    if args.all_sessions and args.repo:
        print("error: --all-sessions cannot be combined with --repo", file=sys.stderr)
        sys.exit(2)
    if args.since:
        if args.window:
            print("error: --since cannot be combined with --window", file=sys.stderr)
            sys.exit(2)
        since = parse_ts(args.since)
        if since is None:
            print(f"error: invalid --since '{args.since}' (use ISO 8601 UTC)", file=sys.stderr)
            sys.exit(2)
        start, end = since.astimezone(timezone.utc), datetime.now(timezone.utc)
    else:
        start, end = parse_window(args.window)
    claude_homes = [Path(h).expanduser() for h in (args.claude_home or DEFAULT_CLAUDE_HOMES)]
    claude_homes = [h for h in claude_homes if (h / SESSION_DIR).is_dir()]
    if not claude_homes:
        print("error: no Claude Code session history found", file=sys.stderr)
        sys.exit(1)
    out_dir = Path(args.out).expanduser()
    transcripts_dir = out_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    repos = [] if args.all_sessions else resolve_repos(args.repo)
    skills = discover_skills(repos, claude_homes, args.skills_dir)

    test_matchers = [re.compile(p, re.I) for p in GENERIC_TEST_PATTERNS]
    user_matchers = []
    for pattern in args.test_pattern:
        try:
            user_matchers.append(re.compile(pattern))
        except re.error as exc:
            raise SystemExit(f"error: invalid --test-pattern '{pattern}': {exc}")
    script_cache = {}

    def scripts_for_cwd(cwd):
        repo = session_repo(cwd, repos)
        if repo is None:
            return set()
        if repo not in script_cache:
            script_cache[repo] = discover_test_scripts([repo])
        return script_cache[repo]

    sessions = []
    in_scope_count = 0
    files = find_claude_session_files(claude_homes, start)
    for mtime, path in files:
        if has_review_command(path):
            continue
        parsed = parse_claude_session(path, start, end, test_matchers, scripts_for_cwd, user_matchers)
        if parsed is None:
            continue
        meta, stats, entries, skills_used = parsed
        # why: a session that holds only /clear or /model has nothing to score
        # why: such a session gives free scores and lowers skill_coverage
        if stats["assistant_turns"] == 0:
            continue
        # why: a trial starts many claude -p runs, and each run is a probe, not a workflow session
        if meta.get("headless") and not args.include_headless:
            continue
        if not args.all_sessions and not session_matches_repos(meta.get("cwd"), repos):
            continue
        in_scope_count += 1
        sessions.append({
            "meta": meta,
            "stats": stats,
            "skills_used": skills_used,
            "file": str(path),
            "modified_at": mtime.isoformat(),
            "_entries": entries,
        })

    if args.all_sessions:
        repos = infer_session_repos(sessions)
        skills = discover_skills(repos, claude_homes, args.skills_dir)
    installed_skill_names = set(skills)
    for session in sessions:
        detected = detect_skills_from_entries(session["_entries"], installed_skill_names)
        # why: Claude Code calls a plugin skill "plugin:skill", and the inventory holds "skill"
        called = {n.split(":")[-1] for n in session["skills_used"]}
        session["skills_used"] = sorted((called | detected) & installed_skill_names)

    sessions.sort(key=lambda session: session["modified_at"], reverse=True)
    for s in sessions:
        tpath = transcripts_dir / f"{Path(s['file']).stem}.md"
        log_repos = list(dict.fromkeys([r for r in [session_repo(s["meta"].get("cwd"), repos), *repos] if r]))
        git_logs = [(r, git_log_patch(r, s["stats"]["first_ts"], s["stats"]["last_ts"])) for r in log_repos]
        tpath.write_text(render_transcript(s["meta"], s["stats"], s["skills_used"], s["_entries"], git_logs))
        s["transcript_path"] = str(tpath)
        del s["_entries"]

    skill_usage = {name: 0 for name in skills}
    for s in sessions:
        for name in s["skills_used"]:
            skill_usage[name] += 1

    if args.all_sessions:
        scope, scope_name = "all", "all-sessions"
    else:
        scope = "repos"
        scope_name = repos[0].name if len(repos) == 1 else "multiple-repos"

    inventory = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claude_homes": [str(h) for h in claude_homes],
        "session_scope": scope,
        "repo": str(repos[0]) if len(repos) == 1 else None,
        "repos": [str(repo) for repo in repos],
        "repo_name": scope_name,
        "repo_names": [repo.name for repo in repos],
        "window": {"arg": args.window or (f"--since {args.since}" if args.since else ""), "start": start.isoformat(), "end": end.isoformat()},
        "skills": sorted(skills.values(), key=lambda x: x["name"]),
        "skill_usage": skill_usage,
        "stats": {
            "session_files_scanned": len(files),
            "sessions_in_scope": in_scope_count,
            "sessions_written": len(sessions),
            "skills_found": len(skills),
            "skills_used": sum(1 for v in skill_usage.values() if v > 0),
        },
        "sessions": sessions,
    }
    (out_dir / "inventory.json").write_text(json.dumps(inventory, indent=2))

    st = inventory["stats"]
    print("scope:             " + ("all sessions" if args.all_sessions else ", ".join(str(r) for r in repos)))
    print(f"window:            {start.isoformat()} -> {end.isoformat()}")
    print(f"skills found:      {st['skills_found']} ({st['skills_used']} used in window)")
    print(f"sessions written:  {st['sessions_written']} -> {transcripts_dir}")
    print(f"inventory:         {out_dir / 'inventory.json'}")


if __name__ == "__main__":
    main()
