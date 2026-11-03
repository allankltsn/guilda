# Full GitHub Projects registration contract

GitHub Projects is the durable execution/acceptance record when selected. Every card is
a GitHub issue added to one configured project (user or organization level), so work
spread across several repositories lives on a single board. The issue is created in the
repository where the work happens; the project groups them. Code, evidence files and
logs stay in the authorized workspace/worktree and are linked from the issue, never
pasted in full. Only the principal changes project configuration (fields, options,
views, built-in workflows) through an authorized proposal.

## Project configuration (see integrations/github-projects)
| Field | Type | Values / meaning |
|---|---|---|
| Status | Single select | open, pending, in-progress, in-review, rejected, blocked, completed, accepted, closed — exactly these nine; remove the default Todo/In Progress/Done |
| Priority | Single select | critical, high, medium, low |
| Type | Single select | epic, story, task, bug, spike |
| Estimate | Number | story points or size; set by product-owner, revisited when scope changes |
| Agent | Text | function · portable instance token (agents are not GitHub users) |
| Sprint | Iteration | optional; replaces per-sprint directories |
| Due date | Date | optional |
| Completed at | Date | set only by the principal when moving to completed |

GitHub assignees identify humans only; never invent accounts for agents. Parent/child
uses native sub-issues: the parent milestone issue is "Task N", participant issues are
its sub-issues. Built-in project workflows that change Status automatically (item
closed -> Done, pull request merged, item reopened) are disabled: status follows the
authority table below, not repository events. "Item added to project" may set open.

## Issue format
Title: `[<id>] <task>`, e.g. `[task-3-qa] Validate login throttling`. Body follows
templates/issue.md: scope, criteria checklist, time, evidence links, findings and
decisions, problems/causes/solutions and human acceptance. Prior status on blocks,
checkpoint timestamps and verdicts stay in the body or in comments, never only in a
field. UTC ISO 8601 timestamps.

Stories and epics (workflow/user-stories.md, templates/user-story.md): `[S-NNN]` and `[E-NN]`
titles, Type field story/epic, tasks are sub-issues of the story, stories are sub-issues of the
epic. In a multi-repository product (workflow/polyrepo.md) stories live in the hub and tasks in
the repositories that change; the Project groups them. A story is dispatched only after
Definition of Ready and moves to completed only after Definition of Done.

IDs: task-N, task-N-impl, task-N-impl-cpK, task-N-review, task-N-qa,
task-N-security, task-N-fix. The ID lives in the title and in the label task-N; the
GitHub issue number is the link, not the identity. Labels role:<function>, type:<epic|story|bug|spike>, tier:<deep|standard|light>
(optional, for cost reviews), task-N, checkpoint; retroativo for explicit retrospective registration, abandonado for
abandoned work. Retroactive records never imply contemporaneous evidence.

Read-only participants return complete issue updates, reports and sanitized evidence
to the principal instead of calling the GitHub API or bypassing tool/sandbox
restrictions. The principal persists these records faithfully, retaining the
originating instance, snapshot, timestamps and verdict; persistence never transfers
authorship or approval. Apply this handoff to every registration step below when
writes are unavailable.

## Access
Writes use the GitHub CLI (`gh issue`, `gh project item-edit`; token with `repo` and
`project` scopes) or GitHub MCP tools that support Projects. Detect what is available;
never request broader scopes, never store tokens in issues, files or logs. If the
board cannot be written, the card stays with the principal as a complete pending
update and the gap is recorded as blocked — never fall back silently to another
tracker.

## States and authority
| State | Meaning | Who transitions |
|---|---|---|
| open | Planned, not scheduled | Principal |
| pending | Brief ready | Principal |
| in-progress | Work active | Assigned instance before acting |
| in-review | Delivered for validation / validation active | Author submits; validators start |
| rejected | Defect returned for correction | QA/reviewer/security |
| blocked | Impediment or pending user decision | Detector, informing principal |
| completed | Technically verified with evidence; awaiting human acceptance | Principal |
| accepted | Explicitly accepted by user | User or principal recording written decision |
| closed | Sprint-review closure or explicit abandonment | Principal |

The issue stays open through accepted. Moving to closed also closes the issue
(reason completed; not planned with label abandonado). Never use Done. Set operational
state before the corresponding action. Completion states follow actual evidence, not
advance declarations. Specialist never promotes own issue beyond in-review;
rejected/blocked are exception routing states. Checkpoint execution-finished is a body
timestamp/checklist and evidence; Completed at is reserved for principal-verified
completed. GitHub does not enforce who moves a card: text never proves enforcement,
so the principal audits Status changes in the project history at verification.

## Procedure
1. Principal creates the parent milestone issue and participant sub-issues before
   dispatch, with role, permitted paths, criteria and next owner, and adds them to the
   project. Ready -> pending; assignee instance marks in-progress before acting.
2. Agent reads the issue and updates next owner. For a substantial scoped task create
   3-8 capability checkpoint sub-issues, not micro-steps; proportional simple task may
   record the checklist in the parent with explicit rationale. Mark active before work.
3. Author stores real sanitized evidence in the repository before handing back, links
   it, and fills time/evidence/decisions. Checklist completion is not self-approval.
4. QA, compliance/technical review and security have separate issues/instances.
   Findings route to the responsible fixer; blocking ones get a rejected fix issue.
5. Principal reexecutes at least one evidence command, checks snapshot/commit and
   required gates, then moves completed. Divergence returns work in-progress with
   recorded difference. No evidence -> blocked, no invented completion.
6. Accepted requires user identity/date/scope/decision in the body or a comment from
   the user. Closed is Sprint Review or explicit abandonment with label and reason.

## Board freshness and dual validation
A board that nobody updates is not a record. Because built-in workflows are off, Status moves only when
an actor moves it, so freshness is a duty with owners. Defaults below; a project may override the windows
in its instructions.

- **Stale** means no Status change, comment, evidence link or LOG event within 24 hours for `in-progress`
  and `in-review`, 7 days for `pending` and `blocked` (a card waiting on a user decision shows the date of
  the question), and 30 days for `open`.
- **Demand owner** (the `product-owner` for stories and epics, otherwise the principal) confirms the card
  still represents a live request: outcome, priority and criteria are current. Otherwise rewrite it or
  move it to `closed` with the `abandonado` label and a reason.
- **Delivery owner** (the specialist instance assigned in the Agent field) confirms Status, evidence links
  and next owner reflect the real work. The principal persisting an update for a read-only participant
  does not count as the delivery owner's attestation.
- **Independent cross-check by the principal.** It reads both attestations against the project history,
  the handoffs and the evidence, flags every irregularity (stale, Status ahead of evidence, missing owner)
  and records the result. A card is validated only when both owners attested inside its window.
- **Review whenever a crash-safety record is written.** When the principal writes a handoff (every
  project with this profile), a diary entry or the live state (when `session-continuity` is selected), it
  reviews the board in the same step: (1) every `in-progress` and `in-review` card has a live agent or a
  handoff file; a lost agent moves its card to `blocked` (prior status in the body, `LOG PROBLEMA`), or to
  `pending` when a replacement will be dispatched; (2) Status and evidence match what was just recorded;
  (3) stale cards are attested, moved or closed with a reason; (4) each move is a `LOG` event and follows
  the authority table above.
- **Also review** at session start or resume, at the end of each wave and before verification. Record one
  line with the number of cards checked, stale, moved and waiting on a decision.

## Severity mapping
Canonical findings: Critical / High / Medium / Low; retain source severity verbatim.
Legacy Critical -> Critical. Legacy Important -> High unless documented impact
justifies Medium; legacy Minor -> Low unless documented impact justifies Medium.
Record rationale and impact when mapping, never silently downgrade. Critical/High
block completion until corrected/revalidated or an explicitly authorized risk
decision where appropriate; all pending findings/recommendations need disposition.

## Mandatory records
- Parent issue postmortem: every real problem/decision, cause, solution that worked,
  failed attempts and prevention. Per-issue minutes in body.
- Principal event log: comments on the parent issue, one event per comment, formatted
  `LOG <TYPE> | <UTC> | <instance> | <issue id> | <message> | <evidence link>`.
  Types INICIO, MARCO, RED, GREEN, ESCOLHA, DESVIO, RISCO, PROBLEMA, SOLUCAO,
  DECISAO, ALERTA_PERIGO, FIM. At closure summarize the log in the parent postmortem.
- User decision: blocked with DECISAO prefix in the title, prior status in the body,
  context/options/recommendation/consequence if unanswered; return NEEDS_DECISION and
  the issue URL. Principal informs user; unaffected authorized work continues. On
  decision record applied scope, remove prefix and resume prior appropriate state.
- Dangerous actual action: do not execute, CRITICIDADE ALTA/CRITICA in the issue,
  assessment and principal notification immediately; log ALERTA_PERIGO.

## Visibility
Issues and comments inherit the repository's visibility, and a public project is
readable by anyone. Never place secrets, private endpoints, personal data or
unsanitized output in issues, comments or field values; link sanitized evidence
files instead. Keep the project private unless every linked repository is public.

## Evidence files and coverage
Configured evidence root/sprint/issue in the repository:
implementer evidence + test-output; infrastructure compose-ps/probe/logs; database
migration-check including applied schema and seed twice only when relevant/authorized;
review report with snapshot/findings/file:line/verdict; QA report + raw output;
security report + coverage; fixer failing-before/passing-after evidence; investigator
findings/cause/confidence; principal verification with command reexecution.
All include exact command/cwd/snapshot/UTC/exit code, raw sanitized output, criterion
mapping and not-verified items. See policies/evidence.md and templates.
RED must represent valid behavior failure, not unavailable prerequisite; check Docker
first only if selected tests need Docker. Do not mandate Docker for every stack.

## Migration from Kanban Markdown
Existing Markdown cards import as issues: frontmatter id -> title prefix and task-N
label, status -> Status (legacy backlog -> open), priority -> Priority, assignee ->
Agent, epic -> parent issue, dueDate/completedAt -> date fields, labels -> labels; the
body is kept verbatim. Import is a principal action with recorded mapping; the original
files are left untouched until the user decides otherwise.

## Availability, scope and checklist
If inactive for roughly 10 minutes, principal records last activity and investigates
through authorized provider status/logs; portable handoff never depends on private
Claude transcript paths. Pending required permission -> blocked/decision; do not
expand permissions. New required paths go to principal for authorized scope change.
Prefer bounded rg/path searches; avoid unbounded dependency/root recursion.
Shared migrations/lockfiles/root config/compose have one owner. Parallel writes disjoint.

Before return: issue exists in the project with role/scope/criteria; active status
preceded work; checkpoints/checklist recorded; real evidence saved and linked;
time/postmortem/next owner filled; decisions/danger/limitations communicated; issue
not self-approved.
