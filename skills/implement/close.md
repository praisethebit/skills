# Close and ship

   - Write the `## Answer`. It holds one line for each acceptance criterion: the criterion and its proof (the command, the test or the observation, and its result). A criterion with no proof is a gap. List a gap only when the user accepted it in an `AskUserQuestion` answer. A gap with no such answer is a blocker: ask now, before `close-issue`. The Answer says what changed and names the lasting facts in the README, the config, the behavior spec file (for each behavior fact) or a `why:` comment (only for a fact about an external tool that the code cannot show, or about our own design that no test name or doc can hold), as code-format paths (no Markdown link). It holds one line for each new guard: the guard and the failure that it catches. A guard that a criterion names is mandatory. The Answer has a `### Rulings` list as its own subsection: one line for each ruling, with 3 parts: what you decided, why, and the cost if the decision is wrong. With no ruling, write "None." Then run `~/.claude/bin/close-issue NNN`. Do not read the tracker doc for this step.
   - Call `commit-push` one time with all changed paths, the issue files included. Include each `edited:` path that `close-issue` prints.
   - Put every issue file that you created or edited in this session in the same `commit-push` call.

   Use two commits only when a live check needs the push first (for example a deploy that pulls from git): ship the work, do the live check, then close the issue and ship the close.

   If the live check needs a test commit (a forced failure or a removed resource), ship the revert and the close in one commit.

   The final message is the chat message after the last `commit-push` call (the one that ships the close). It holds these 5 parts and no other part:
   1. The result: the issue is closed and shipped, in one line. The line holds the number and the title of the issue. The title is the text of the `# ` line of the issue file. When the push of `commit-push` failed, the line says that the commit is not pushed.
   2. The change: 1 or 2 sentences on what is different in daily use for the user. It says what the user now sees, gets, or does not do anymore. It names no file path, no commit hash and no count. It can name a command or a skill that the user types. When the change has no effect in daily use (for example a removal, a refactor or a test), the part says that daily use does not change, and names in one sentence what the change protects or prepares.
   3. Each thing that needs the user: each accepted gap, each new follow-up issue with its number, and each decision that waits for the user. A new-issue question is not a waiting decision: step 4.7 asks it before `commit-push`.
   4. Each ruling with a real cost: one line with what you decided and the cost if the decision is wrong. A ruling has a real cost when a wrong decision changes the result for the user, or when its undo needs work. A ruling with "Cost if wrong: none" has no real cost.
   5. The next action: the one thing that the user does next, for example "run `/clear` before the next issue".

   Write the final message in this shape:

   ```
   Issue NNN (<title of the issue>) is closed and shipped.
   - Changed: <1 or 2 sentences of part 2>
   - Needs you: <each item of part 3, or "nothing">
   - Rulings with a real cost: <one line for each, or "none">
   - Next: <the one next action>
   ```

   When you are not sure that an item needs the user (part 3) or that a ruling has a real cost (part 4), the item stays in the message. These parts stay out of the final message, and the `## Answer` holds each of them that exists before `commit-push`: the commit hashes, the state of the push, the list of the tests, the count of the review findings, the counts of the change (files, lines, items), the detail of the change (each changed file and each step of the work, not the `Changed:` line) and each ruling with no real cost. The `## Answer` keeps each ruling with its 3 parts.

   This content list applies only to the final message. A message that stops the session before that `commit-push` call (a blocker, an escalation, a stop for a different model, an issue that is not clear) keeps its full content.
