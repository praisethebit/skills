---
name: Outcome
description: 'Whether the session delivered what the user asked, and whether the "done" statements of its last message are true.'
labels:
  - value: 'delivered'
    description: 'Each request item has a result that the transcript shows, or a gap that the user accepted. Each statement in the last message agrees with the tool output.'
    score: 1
  - value: 'incomplete'
    description: 'One or more request items have no result or no proof, and the last message says so.'
    score: 0.4
  - value: 'false_done'
    description: 'The last message says "done" or "pass", but an item is missing, has no proof, or a tool output disagrees.'
    score: 0.2
  - value: 'insufficient_evidence'
    description: 'The session asks for no result (a question only), or the user stopped it before the end.'
    score: 0.5
---

**Rubric**

You score one condensed transcript of a local coding-agent session. Judge 2 things only:

1. **Cover of the request.** Each request item has a result that the transcript shows, or a gap that the user accepted.
2. **Truth of the last message.** Each statement in the last message of the agent agrees with the tool output in the transcript.

Find the request:

- **Source.** The request of an `/implement` session is the acceptance criteria of the issue file, and each later user message that adds work. Find the criteria in the `Read` output of the issue file. The request of each other session is the user messages.
- **Criteria not visible.** When the transcript cuts the issue file (for example a `cat` in Bash), judge the criteria that the transcript shows and the statements of the last message. Count no missing criterion as a gap.
- **2 or more requests.** The worst request sets the label. When the user changed a request, the last version counts.
- **Stop by a rule.** A session that stops by a rule gets `incomplete`: an escalation, or a blocker that gets no answer. Outcome measures the delivery, not the blame. This rule wins over `insufficient_evidence`: a session that ends on a blocker question with no answer is `incomplete`.
- **Silent gap.** A last message that names no gap and gives the work as finished is a "done" statement. When a request item is missing, the label is `false_done`.

Scoring rules:

1. Judge against the request of the user, not against what the agent could add.
2. A simple task that the agent did correctly gets `delivered`. Do not invent a gap.
3. When the request was ambiguous and the agent stated its reading, do not lower the label for that reading.
4. An error that the agent found and fixed before the last message does not count. Efficiency scores the rework.
5. The tool output is the truth. When a statement of the agent disagrees with a tool output, the tool output wins.

Out of scope: the quality of the code (scored under Code Quality), the test runs (scored under Test Quality), the rework (scored under Efficiency), the skipped steps (scored under Procedure Compliance) and the length of the text (scored under Verbosity).

**Reason**

One to three sentences. Name each request item with no result or no proof, or the statement of the last message that a tool output disagrees with. Quote the tool output. For `delivered`, name the evidence for the request items.
