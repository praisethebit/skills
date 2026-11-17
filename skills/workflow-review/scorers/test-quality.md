---
name: Test Quality
description: 'Whether the agent ran the right tests at the right time, wrote the right number of tests, and wrote tests that catch a broken implementation.'
labels:
  - value: 'effective'
    description: 'The agent ran the tests at the right times, wrote each guard that the guard rule asks for and no other test, and the guards would fail on a broken implementation.'
    score: 1
  - value: 'wasteful'
    description: 'The agent ran too many tests or wrote tests that the guard rule does not ask for: the full suite after each small edit, a second run with no change, or a test with no failure that it catches.'
    score: 0.4
  - value: 'insufficient'
    description: 'A guard that the guard rule asks for is missing, the agent ran no proof before it said the work was done, or the guards are not effective: they assert trivia, or they mock the logic under test.'
    score: 0.2
  - value: 'insufficient_evidence'
    description: 'The session has no test run and no code change, or the code change has no behavior to test (for example a text edit).'
    score: 0.5
---

**Rubric**

You score one condensed transcript of a local coding-agent session. Judge the tests that belong to the code change: the test runs (marked in the transcript with the command, the result and the duration), and the tests that the agent wrote or changed. If the session has no test run and no code change, the label is `insufficient_evidence` and the session is excluded from aggregation. A session with a code change and no proof (no test run, lint, validate step, dry run or device check) is `insufficient`, unless the change has no behavior to test (for example a text edit in a doc or a skill). A code change with no new guard is correct when the guard rule asks for no guard. Do not give `insufficient` for that. A change with no behavior to test and no test run is `insufficient_evidence`.

Assess:

- **Run frequency.** The agent ran a sufficient targeted test. It did not run the full suite after each small edit. A full suite is right before the work is done, or when the change touches shared code.
- **Run timing.** The agent ran the tests before it said "done". It did not run the same tests a second time with no change in the code between the two runs. A run after a fix is correct.
- **Creation.** The guard rule: a new test (a guard) is correct only when the session can name, in one sentence, the failure that it catches. That failure is one that a user or a different part of the system sees, that a later change can cause with no compile or lint error, and that the test reaches through a public interface. An edge-case guard is correct only when it comes from a real bug, when the failure loses data, breaks security or damages a host, or when the acceptance criteria name it. A test of a private function, of a value copied from the code, of a one-time migration or of text is a waste. A failure that meets the guard rule and has no guard is a defect. No guard is correct when no failure meets the guard rule, also when the session states no reason.
- **Effectiveness.** A broken implementation would fail the tests. The tests do not assert trivia and do not mock the logic under test. Each guard is at the lowest level that shows the failure: a unit test first, and a browser or device test only for a main user path or for a behavior that only a real browser or device shows. They are not so tied to internals that an unrelated change breaks them.

Out of scope: the quality of the non-test code (scored under Code Quality), and the other waste in the session (scored under Efficiency).

Out of scope: whether the "done" or "pass" statements of the last message are true (scored under Outcome).

**Reason**

One to three sentences. Name the run count and the test files that drove the label. Name what would have prevented a defect: a repo test script, a rule in `AGENTS.md`, or a skill.
