# Economy mode: spend fewer tokens without removing a gate

Economy changes HOW work is executed, never WHETHER it is verified. Everything in
workflow/engineering.md still holds: no gate is removed to save tokens; the principal never
implements or approves its own work; validators inspect the same snapshot; silence, timeout and
an exhausted budget are never approval; no gate runs below `standard` (policies/models.md).
If a rule below conflicts with a gate, the gate wins and the cost is accepted.

## Rules
1. **One author at a time.** At most one agent writes. Two may run in parallel only when their
   write scopes are disjoint AND each has a small context. Never fan out a whole wave at once.
2. **Brief by reference.** A dispatch is at most ~15 lines and points to files: the spec/plan, the
   findings file and, when needed, a brief file (templates/brief.md). Do not paste the shared
   context again for each agent.
3. **Handoff in a file.** Every agent ends by writing a short summary (at most 40 lines: files
   touched, IDs handled, commands run and results, pending items; templates/handoff.md) to
   `docs/operations/handoffs/<task>-<date>.md` and returns to the principal only the path plus 5
   to 10 lines. A rerun overwrites its own handoff (policies/quality-principles.md, idempotence). After writing the handoff, the principal reviews the board as in workflow/github-projects.md (board freshness).
4. **Do not resume a heavy agent.** Resuming reloads the whole history. If an agent already used
   about 150k tokens (default; a project may override it in its project instructions), or was cut off by a session or rate limit, do not resume it: dispatch a NEW
   agent with a small, closed task that reads the handoff and the findings file. Resume only for a
   short adjustment to a light agent. This keeps the same author-and-gate independence: a new
   author is still never its own validator.
5. **Scope before suite.** While writing, run only the tests of the touched scope plus the fast
   static checks (type check, lint, format). The full suite, slow end-to-end or browser runs and
   screenshots run once at the end of the wave or in the final QA, on the final snapshot.
6. **Heavy evidence only at the end.** Screenshots and visual comparisons belong to the final QA
   with a stated sample (critical screens, sizes and themes), not to every wave.
7. **Gates once per snapshot.** After a correction, revalidate only the gates the delta affects
   (workflow/engineering.md, correction and convergence), with a new snapshot manifest. Read-only
   gates (technical review, security, privacy) may run in parallel with each other; QA runs last.
8. **Tiers.** Authors and QA in `standard`; `light` for mechanical bookkeeping; `deep` per policies/models.md
   (typically security/privacy judgment and irreversible decisions). Record `Model tier: <tier> - <reason>`
   in the brief.
9. **Lean reports.** Agents return verdict + IDs + paths; details go to a file. No pasted test
   output or diffs.
10. **Principal context.** Keep the principal's own context small: read by path and line range,
    use output-compressing tools only when installed and registered (policies/installations.md),
    and compact the conversation at wave boundaries.
11. **Budget check per wave.** At the end of each wave the principal records one line: tokens per
    agent (the `usage` field of each report, when available) and whether a session limit was
    hit. If one agent exceeds about 250k tokens (default; overridable per project), split its task in two.
12. **Cheap bookkeeping.** Tiny records (one line, one citation, one status) are appended directly
    by the principal (`echo >>`, `sed`) without dispatching an agent: a bookkeeping agent often
    costs tens of thousands of tokens mostly to reread large files. Use the scribe role only when
    the text requires reading documents. This never replaces specialists for judgment, gates or
    implementation.

## What economy never does
- Skip, merge or downgrade a gate, or let one agent both author and approve.
- Reuse a validation verdict for a changed snapshot without an impact analysis.
- Treat a cut-off or silent agent as done: it is a failure to handle (policies/quality-principles.md).
- Hide uncertainty: unverified work is reported as unverified.

Session-level budgeting (token milestones, resume points after a crash) is in
workflow/session-continuity.md.
