# Session continuity: token milestones and resume points

Binding only when the project selects the `session-continuity` profile (opt-in); the file is
installed with the core in every project but is informational otherwise. The rules protect
long sessions from silent budget exhaustion and from external failures (crash, power loss, lost
connection). They add no gate and remove none; workflow/engineering.md and workflow/economy.md
still apply.

## Token milestones
Count cumulative session usage: the principal session plus its subagents (sum the `usage` field of
agent reports and read the interface's context indicator). The agent usually has no exact
counter: use the best available indicator and, when in doubt, treat the milestone as reached.
An automatic counter is optional (integrations/token-milestones/README.md).

Thresholds are configurable per project; the defaults are:

| Milestone | Default | Action |
| --- | --- | --- |
| ask | 100k, 200k, 300k | Finish the step in progress, then ask the user whether to end the session. |
| mandatory | 400k | No question. Run the closing protocol below. |

**Ask milestones.** Present a button/choice question, recommendation first, with the reason:
"End the session now?" with (a) "Yes: finish current executions, record what is needed in project
memory and write the new-session prompt" (recommended when the context is already heavy or a
logical phase just closed) and (b) "No: continue to the next milestone". If the user continues,
ask again at the next ask milestone. The user decides.

**Mandatory milestone.** Do, in this order, without asking:
1. Dispatch no new agent; let running agents finish and record their results.
2. Record in project memory everything the next session needs (state, hashes, decisions,
   pending items).
3. Write the continuation prompt (templates/continuation-prompt.md) to
   `docs/operations/continuation-prompt-<YYYY-MM-DD>.md`: what to read first, current state,
   next step, what NOT to do.
4. Stop and tell the user the prompt path and that the session should be closed and another
   started. The agent cannot close the session itself.

"Finish current executions" means: wait for already dispatched agents and record their results;
start no new work. Exhausted budget is never approval of pending gates (workflow/engineering.md).

## Resume points against external failure
The machine or the connection can drop without warning. Keep these artifacts so the next session
resumes without losing direction:

- **Event diary (append-only).** `docs/operations/session-diary-<YYYY-MM-DD>.md`
  (templates/diary.md). Append ONE short line (time, event, path of the handoff or file) at each
  fixed point: before dispatching an agent (intent and brief path), when an agent report arrives
  (verdict and handoff path), and when a gate opens or closes. Only append, never rewrite: a crash
  loses at most the last line.
- **Live state (short, overwritten).** `docs/operations/live-state.md` (templates/live-state.md),
  at most 25 lines: current phase, current snapshot hashes, agents in progress, next step, pending
  items for the user. Update at each phase or gate change, writing a temporary file first and
  renaming it over the old one (atomic replace), so a crash never leaves a half-written state.
- **Board review with every record.** Each diary entry and live-state update is followed by the board
  review in workflow/github-projects.md (board freshness and dual validation), so a crash never leaves
  cards ahead of or behind the real state.
- **Project memory only at milestones** (end of a round, a user decision, token milestones), not at
  every event, to save tokens.
- **Mechanical records by direct append** (`echo >>`), without an agent; use the scribe only for
  text that requires reading documents (workflow/economy.md, rule 12).

## Resuming after a crash
1. Read `live-state.md` and the tail of the diary.
2. An agent that was in progress is considered LOST. Check whether its handoff exists as a file.
3. If the handoff exists, continue from it. If not, dispatch a NEW agent with a closed task; never
   resume the old one (workflow/economy.md, rule 4).
4. Revalidate the snapshot hash in `live-state.md` against the working tree before trusting any
   earlier gate verdict; a changed snapshot needs gate impact analysis.
5. Add a diary line stating the resume and what was found.
6. Review the board (workflow/github-projects.md, board freshness): an agent given up as LOST must not
   leave its card `in-progress`.

## Privacy of the records
Diary and live state hold event types, times, statuses and paths relative to the project root
(never absolute or user-home paths). The short description comes from the brief's title or ID,
never from prompt text. Never write prompt text, tool output, secrets or personal data into them (policies/safety.md).
