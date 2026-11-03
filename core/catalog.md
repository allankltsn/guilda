# Preservation matrix
Source paths relative to original checkout; targets relative to core. Every
substantive role body is retained with provider frontmatter removed, project values
parameterized and explicit profile/authorization/independence conditioning.
No installed-version/runtime/parity claim follows from source presence.

| Source | Canonical target | Preservation |
|---|---|---|
| .claude/agents/architect.md | roles/architect.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/aws.md | roles/aws.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/backend.md | roles/backend.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/cicd.md | roles/cicd.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/cloud.md | roles/cloud.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/deployment.md | roles/deployment.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/devsecops-infra.md | roles/devsecops-infra.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/docker.md | roles/docker.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/finops.md | roles/finops.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/hosting.md | roles/hosting.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/ingress.md | roles/ingress.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/kubernetes.md | roles/kubernetes.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/orchestration.md | roles/orchestration.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/python.md | roles/python.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/qa.md | roles/qa.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/security.md | roles/security.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| .claude/agents/sre.md | roles/sre.md | Complete substantive body, checklists, commands, references and output; profile-conditioned, provider metadata removed |
| New requirement | roles/reviewer.md | Independent compliance and technical review, qualified expertise required |
| .claude/commands/{qa,security,aws,hosting,kubernetes,sre,cicd,devsecops-infra}.md | actions/<same-id>.md | All eight intents/arguments/results; corrected snapshot/base handling |
| CLAUDE.md | policies, workflow, profiles | Stack knowledge, routing, Superpowers phases, security/approval and independent gates |
| docs/sprints/board-workflow.md | workflow/github-projects.md, templates/issue.md | Card -> GitHub issue in one Project; Status/fields instead of frontmatter, states, ownership, checkpoints, evidence, logs/time, decisions, verification, postmortem |
| skills/drawio-diagram/SKILL.md | skills/drawio-diagram/SKILL.md | XML skeleton, nodes/edges/groups, styles/fallback, context and output; paths/inputs parameterized |
| .claude-plugin/{plugin,marketplace}.json | Adapter distribution responsibility | Metadata/package structure; personal identity/repo excluded from core |
| .claude/settings.local.json | policies/integrations.md | Permission/worktree awareness, eight Voltagent packs; personal allowlists not copied |
| .serena/project.yml | policies/integrations.md | Language/backend/workspace/ignore/tools/modes; no memory/state copied |
| .vscode/settings.json (Kanban Markdown) | integrations/github-projects, workflow/github-projects.md | Superseded: columns become Status options; legacy Markdown cards import via explicit mapping; personal Python settings excluded |

QA owns functional/contract/regression and incidental auth failures; security owns
systematic IDOR; devsecops-infra owns IaC; cloud selects services, AWS implements.
Ingress covers Nginx/Traefik/ALB/Gateway API; hosting is profile-conditioned.
Orchestration is service mesh; principal coordinates AI agents.
Main-thread fixing and repeated per-turn approval are removed. Historical
cost/plan/limit/threshold claims require verification. Local board paths/private
transcripts are not defaults; execution-finished differs from approval.
Original severities retained with explicit mapping; legacy backlog maps explicitly.
Text never proves enforcement; external plugin installation is not inferred.

## Additions in 1.1.0 (generalization and product management)
| Origin | Canonical target | Notes |
|---|---|---|
| Multi-project reuse requirement | roles/architect.md, roles/backend.md, roles/security.md | Project and stack specifics became profile-conditioned; no project name remains in core |
| Per-specialist model choice practice | template.json model_tiers, roles[].tier, policies/models.md | Logical tiers deep/standard/light rendered as Claude model and Codex reasoning effort; per-project overrides |
| Product/UX/brand/marketing/frontend practice | roles/product-owner, ux-researcher, ux-designer, ui-designer, brand-strategist, marketing, frontend-senior | Author mode (no shell) for artifact roles |
| Privacy and health veto in design decisions | roles/privacy-compliance.md, actions/privacy.md, workflow/usability.md | Not legal advice; LEGAL-REVIEW to the human |
| Two simulated lay users (weakest model) and decision brainstorm | roles/lay-user.md, roles/ux-researcher.md, workflow/usability.md, templates/persona.md, usability-report.md, decision.md | Read-only, isolated, light tier |
| Hub repository and split of a monorepo into repositories | workflow/polyrepo.md, profiles/polyrepo.json | Contracts first, one owner per shared artifact |
| Stories with DoR/DoD, assets, metadata | workflow/user-stories.md, templates/user-story.md, actions/story.md, github-projects Type and Estimate | INVEST, Given/When/Then, traceability |
| Installation registry and approval rule | policies/installations.md, templates/registro-instalacoes.md, integrations/plugins | Criteria: need, provenance, adoption, security read, scope, reversibility |
| Staffing as a recorded decision | workflow/staffing.md, templates/staffing.md, brief.md Model tier | Team shapes per work type |
| Delivery quality bar | policies/quality-principles.md | Reuse, idempotence, fault tolerance, scalability, simplicity, verifiability |
| Mechanical bookkeeping delegated cheaply | roles/scribe.md | No judgment, no approval |

## Additions in 1.2.0 (operating practices)
| Origin | Canonical target | Notes |
|---|---|---|
| Token-saving orchestration practice | workflow/economy.md, templates/brief.md, templates/handoff.md | Changes how work runs, never whether it is verified; no gate removed; core (always rendered) |
| Session token milestones and crash-resume records | workflow/session-continuity.md, profiles/session-continuity.json, templates/diary.md, live-state.md, continuation-prompt.md | Opt-in profile; configurable thresholds; closing protocol is mandatory at the last milestone |
| Linked IDs, plain-language sentences, recommendations in questions | policies/communication.md | Core (always rendered); language of the user for messages |
| Automatic counter and diary mechanism | integrations/token-milestones/README.md | Specification only; not verified; installing it needs policies/installations.md |

Choice recorded: economy and communication are core because they are low-friction and remove no
gate; session continuity is a profile because it interrupts the user at thresholds and
mandates a stop, which not every project wants. The continuity workflow file is still rendered
in the core tree (all core files are), but it binds the project only when the profile is selected.

## Additions after 1.3.0 (diagram skill)
| Origin | Canonical target | Notes |
|---|---|---|
| Animated architecture/flow diagrams for the template walkthrough (assets/) | skills/dark-pipeline-svg/SKILL.md | Dark design system (palette per group, SMIL patterns, header/status/legend layout); self-contained HTML, provider-neutral output step |
| README/markdown styling (banner, badges, grids, code blocks, Lucide icons) | skills/readme-styling/SKILL.md | Orchestrates dark-pipeline-svg for banner/diagrams/charts; Lucide set in assets/icons/lucide with recolor script |
| Board freshness, dual validation, review with each crash-safety record | workflow/github-projects.md, workflow/economy.md, workflow/session-continuity.md | Boards went stale because nothing moves cards automatically; adds windows, two owners and an independent cross-check |
| SemVer tag before any change lands on main | policies/versioning.md | Tag first, code second; always; principal or designated release specialist tags; no authorization is granted by the rule |
| Secret scans report location, never value | policies/safety.md | File-list/count output only (`files_with_matches`, `rg -l/-c`); mask to confirm; full read needs per-file user authorization; ignore rules can hide `.env` |
