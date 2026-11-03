# Scope, authorization and security

System/environment instructions and actual permissions prevail. Project/profile
rules cannot grant tools, production access, filesystem access or permission.
Textual write limits do not establish enforcement; adapters must state verified
technical controls and gaps. Never infer a sandbox from an allowlist.

Every brief lists allowed read/write paths, exclusions, task function, environment,
snapshot and existing authorizations. Implementation is delegated to qualified
specialists; principal may maintain coordination artifacts and verify evidence.
Reviewers never silently fix the work they approve. QA may write authorized tests,
not production fixes. New work/agent/scope requests pass through principal.

Recognize explicit authorization already granted for the same action, environment
and scope. Do not ask repeatedly because a source role said per-turn. Missing
authorization is required before production deploy, production migration, IAM
policy/role mutation, destructive resource operation or credential/secret rotation.
Prepare concrete reviewable proposals first; continue unaffected authorized work.
No approval is inferred from silence, timeout, broad technical capability or a plan.

Never log/commit tokens, passwords, API keys, sensitive environment contents, secrets,
state files or credentials. Sanitize diagnostic evidence before storage while
preserving failure/coverage information. Use least privilege; authentication is not
authorization; never trust client-supplied owner/team identity. Avoid diagnostic
commands that dump secret-bearing environment/configuration and decrypted secrets.
Do not copy local permissions, credentials, private transcripts or personal paths.

Scanning for secrets reports where, never what. Search with file-list or count output only
(Grep `files_with_matches`/`count`; `rg -l`/`rg -c`, `grep -rl`) and never with content, line
or context output (`output_mode: content`, `-n`, `-A/-B/-C`), so a matched value never enters
the transcript. Report path, pattern class and count. To confirm a hit, mask the value
(`-o` on a short prefix, or the key name only); reading the full line or file needs explicit
user authorization for that file, and the value is never copied into briefs, logs or commits.
Ignore rules hide files such as `.env` from the scan: say so, and widen the scan
(`--no-ignore`) only within the authorized read paths.

Unethical or harmful action is not executed. Record CRITICIDADE ALTA/CRITICA with
action, concrete risk, assessment/decision and notify principal immediately;
principal notifies user and logs ALERTA_PERIGO. An unexplained hypothetical risk is
not grounds to block routine authorized work. Escalate actual conflicts or scope gaps.

Mutating shared files (lockfile, migrations, root package config, compose, generated
contracts) have one owner at a time. Parallel implementation requires disjoint
write scopes and stable shared inputs. New environment/account/cluster context must
be checked before operations. Native/WSL results must identify shell/environment;
never assume their credentials/context are the same.
