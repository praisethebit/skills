---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question. From round 2, give your recommended answer for each question. Round 1 has none (see "Round 1 is open"). Then wait for the user's answers before the next round.

Each round, round 1 included, has this order:

1. A `**State:**` line: what is settled and which round this is. Example: "**State:** Q1 to Q3 are settled. Round 3 has 2 questions."
2. A facts table, only when the round has new facts that you looked up.
3. A maximum of 5 bullets with the conclusions from the facts, only when the table is there.
4. The questions. From round 2, a question holds only the decision, and the `➡️` line holds your recommended answer and one reason. Round 1 keeps its open questions with no `➡️` line (see "Round 1 is open").

Format a round from round 2 like so:

```
**State:** <what is settled>. Round <N> has <count> questions.

<facts table, only when the round has new facts that you looked up>

- <conclusion from the facts, a maximum of 5 bullets, only when the table is there>

❓ **Q1** - **<question title>**: <the decision, with its choices>

➡️ <your recommended answer>. <one reason>

---

❓ **Q2** - **<question title>**: <the decision, with its choices>

➡️ <your recommended answer>. <one reason>
```

Word each question from round 2 so "yes" accepts your recommended answer.

## Round 1 is open

Round 1 has only open questions. A question of round 1 has no recommended answer and no list of options. Why: a recommended answer anchors the user, and the idea must come from the user.

Round 1 covers 3 subjects:

1. Why the user wants this.
2. How it works today.
3. What success is.

**Skip round 1 for a complete issue.** Test the issue file that exists at the start of the grill. When it has an `## Open questions` section or an `## Added findings` section, skip round 1. State what you understood in 2 to 3 lines, before the `**State:**` line. In the same message, start at round 2 with the frontier of the open questions of the issue and of each added finding that needs a decision, each with a `➡️` line. With no issue file at the start, an idea card with neither section, a short request from the user, an issue with neither section, and `/grill-me`, keep the open round 1. The rule on facts below still applies: look up each fact for your recommended answers.

Ask one or more questions for each subject. Keep the `❓ **Q1**` form and write no `➡️` line. When the request of the user or the issue file already answers a subject, ask no question about it: state what you understood. A `Source:` line that names a review finding answers "why". When the request answers all 3 subjects, state what you understood and go on to round 2 in the same message.

For "how it works today", look up the facts yourself (see the rule on facts below). Ask the user only how they use it today and what hurts.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. This holds in round 1 too. When a frontier question needs a fact from the environment (filesystem, tools, etc.), look it up; don't ask the user for anything you could look up yourself. When a few calls settle it, read it yourself. For a search across several files or folders, dispatch the `Explore` agent in the background. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

## Confirmation: failure modes

When the frontier is empty (also at once, when no question needs a decision), do not run a separate failure-mode round. Pick 3 to 5 inputs or conditions that are most likely to break the feature. Each mode names the input or condition and the behavior that a user expects. Put the modes in the message that asks the user to confirm that you reached a shared understanding, in 2 lists. The split is free, and a list can be empty:

```
Guards (become criteria):
- <mode>: <expected behavior>

Declined (go to Out of scope):
- <mode>: <expected behavior>
```

One "yes" accepts both lists. The user can move a mode to the other list, or add a mode, in the reply. After a reply that changes the lists, change them. When the change opens a new decision, ask that decision in a new round. Then send the confirmation message again with the changed lists.

The session is done when the user confirms the message, every branch of the design tree is visited, and nothing is left silently assumed. Do not act on it until the user confirms.
