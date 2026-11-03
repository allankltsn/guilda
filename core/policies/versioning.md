# Versioning: a semver tag before every change that lands on main

Applies to every change that reaches the project's main branch, by any path: merge, push, commit,
cherry-pick, rebase or anything else, when the actor is within scope (the brief lists the paths and the
push authorization). Scope never widens by reading this file: policies/safety.md still governs. Without
authorization, prepare the tag name, the command and the commit as a reviewable proposal and report
`blocked`; do not push.

## Rule
1. **Tag first, code second.** Before the code is pushed or merged to main, create an annotated tag
   `vMAJOR.MINOR.PATCH` (SemVer 2.0.0) on the exact commit that will land, push the tag, and only then
   push or merge the code. Pushing a tag publishes its commit's history objects but does not move main.
2. **Always.** Every change gets a version, including documentation, CI and refactors. Nothing lands on
   main untagged.
3. **Choose the bump from the change, not the effort.**
   - MAJOR: an incompatible change to something consumers depend on (public API, schema, CLI flags,
     file formats or paths that installed projects rely on).
   - MINOR: a backward-compatible capability.
   - PATCH: fixes, documentation, internal changes.
   Tags on main are plain versions. Pre-release suffixes (`-rc.1`) belong to release or feature branches.
4. **One source of truth.** If the project keeps a version in a file (`template.json`, `package.json`,
   `pyproject.toml`), change it in the same commit so the file and the tag match.
5. **Immutable.** A published tag is never moved, reused or deleted without a recorded human decision. A
   wrong version is superseded by the next one.

## Who tags
The principal, after the gates and its own verification of the snapshot being landed, or a qualified
release specialist (for example `cicd`) it designates. An author never tags their own delivery, because
the tag asserts that the snapshot was verified. The tag points to the verified snapshot: if the commit
changes after the verdicts, the verdicts and the tag are redone before anything is published. Only an
unpublished tag may be recreated.

## Failure modes
- Run `git fetch --tags` first. If the next version already exists, take the next free one. A repeated
  run reuses an existing tag only when it points to the same commit (idempotence).
- Tag push fails: do not push the code; report `blocked` with the error.
- Concurrent actors: tags are the arbiter. Whoever publishes first owns the version.

## Record
Write the tag, the commit SHA and the bump reason in the task's evidence (and the changelog when the
project keeps one) before moving the card to `completed`.
