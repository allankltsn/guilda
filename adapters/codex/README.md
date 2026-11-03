# Codex adapter

Project agents are standalone `.codex/agents/<id>.toml` with `name`,
`description`, `developer_instructions`; model selection inherits the session.
Review/diagnostic agents declare `sandbox_mode = "read-only"`; QA declares
`workspace-write`, with a textual probes/tests-only scope that does not enforce
filesystem path boundaries. Implementation uses host defaults and permissions.

The adapter emits `.codex/config.toml` with `[agents] enabled = true`. Existing
different configuration is a conflict: no merge or overwrite is attempted.
Project trust and provider support must be verified in the consuming environment.
`AGENTS.md` explicitly loads shared contracts; each native agent also receives
the common policy instead of relying on inheritance.

Eleven action skills plus the catalog skills (drawio-diagram, dark-pipeline-svg, readme-styling) are emitted into `.agents/skills/`; no identical
Claude slash-command interface is promised. No global settings are changed.

Sources: https://learn.chatgpt.com/docs/agent-configuration/subagents and
https://learn.chatgpt.com/docs/build-skills . Generation/parsing does not prove
discovery, delegation, sandbox enforcement or cross-provider parity.
