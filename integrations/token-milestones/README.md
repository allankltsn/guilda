# Token milestones: optional automatic mechanism (specification)

Status: **not verified in this template.** A reference implementation exists as the optional mod
[token-handoff](../mod/token-handoff/README.md) (`python install.py <project> --mod token-handoff`). It is
unit-tested but has not been verified in a real session, and it simplifies this specification: a single
mandatory milestone at 400k tokens, no ask milestones and no question to the user, and it opens the new
session and ends the old one by itself. The text below remains the original specification.

Purpose: automate what workflow/session-continuity.md asks the agent to do by estimation, without
spending model tokens until a milestone is crossed.

## Shape
A local, per-project hook or mod of the agent runtime (not a package from this template) with two
functions:

1. **Counter.** Read the runtime's session usage, fire each milestone once per session (state kept
   by the mod; reset on a cleared session; not refired after a context compaction), and inject a
   short instruction only when a milestone is crossed (nothing otherwise):
   - ask milestones: instruct the agent to ask the user, at the end of the step in progress, whether
     to end the session (recommendation first);
   - mandatory milestone: deny new calls of the agent-dispatch tool ONLY (no other tool) with an
     explanatory message and inject the closing protocol (workflow/session-continuity.md), at every
     turn after the milestone. The user can disable the mod at any time.
   Known limit to verify per runtime: context size may not include subagent usage, and it drops on
   compaction; a second signal (accumulated cost) may be needed.
2. **Diary.** Append-only lines to the session diary (templates/diary.md) on agent dispatch, agent
   end and milestone crossing. Record only type, short description (truncated, taken from the brief's title or ID, never from
   the prompt text), time, status and paths relative to the project root (never absolute or
   user-home paths); never prompt text, tool results, secrets or personal data. The live state file stays a
   manual artifact of the principal.

Honest limit of this specification: the mechanism cannot close the session. It only blocks new dispatches and reminds. (The token-handoff mod goes further and does close it; see its README.)

## Minimum permissions
No network, no process execution, no secret reads; file access only to append to the diary. (token-handoff is the exception: it executes one PowerShell script and ends the session process, which is why it installs only on explicit request.)

## Installing it
Installation of any kind needs a proposal, security review, explicit user approval and a row in
docs/operations/registro-instalacoes.md in the same turn (policies/installations.md). The
principal never writes the mod itself: a specialist authors it and independent gates (security,
technical review, QA) review the same snapshot.

## Acceptance checks to run before trusting it
Each milestone fires once and does not repeat; the mandatory milestone denies dispatches and
injects the protocol; compaction does not refire milestones; the diary only appends and never
holds prompts or results; with no milestone crossed, nothing is injected; the runtime event for a
finished subagent exists (if not, record the gap).
