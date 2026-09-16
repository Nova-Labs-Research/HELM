# H.E.L.M. roadmap

Current phase: **Phase 0 — Frozen Throne**. Root: `D:\HELM`.

The complete original master checklist is preserved verbatim in
[MASTER_TODO_SOURCE.txt](docs/MASTER_TODO_SOURCE.txt). This file tracks implementation
status; later research goals are not implied complete by the Phase 0 scaffold.

## Phase 0 implementation

- [x] Initialize Git; ignore generated output, environments, and credentials.
- [x] README, MIT license, Python 3.13 selection, virtual environment, dependency file.
- [x] Formatting/linting, standard-library test runner, basic CI workflow.
- [x] All requested source, agent, experiment, fixture, result, and visual directories.
- [x] Copy the supplied generated concept image and embed it in README/CONCEPT.
- [x] Concept, architecture diagram, threat model, safety boundaries, Phase 0 contract.
- [x] Five-state deterministic governance and invalid-transition auditing.
- [x] Identity creation, role lookup, ceilings, expiry, revocation, duplicate rejection.
- [x] Bound authority claims; issuer, target, scope, time, token, delegation and replay checks.
- [x] Immutable global/role policy; deny precedence, review gate, reason codes.
- [x] Deterministic serialized receipts and append-only in-process audit chain.
- [x] Sticky containment, bounded local reasoning, no agent self-release.
- [x] Fixed six-role contract and strict message schema.
- [x] Seeded scenario loading, fault injection, runner, reports, exact replay mode.
- [x] Four experiment scenarios plus independent adversarial fixtures.
- [x] Observable enforcement metrics with documented denominators and nulls.
- [x] Unit, integration, adversarial, and reproducibility tests implemented.
- [x] Complete local verification and record results in `docs/VERIFICATION.md`.
- [x] Initial commit: `chore: initialize HELM research scaffold`.
- [x] Freeze verified Phase 0 with `v0.1.0-frozen-throne`.

## Phase 1 — Raise the Scourge

- [ ] Select first local probabilistic model and implement an isolated adapter.
- [ ] Six fixed roles; synthetic tasks; record every message.
- [ ] No persistent memory, external tools, spawning, or dynamic role changes.
- [ ] Evaluate real behavior separately from deterministic scripted fixtures.

## Phase 2 — Shatter the Helm

- [ ] Inject supervisor timeouts/disappearance, conflicting signals, policy loss,
      delayed/stale authority, and message partitions in the live adapter harness.
- [ ] Measure fragmentation, self-organization, unauthorized continuation, safe halt,
      and coalition formation.

## Phase 3 — Death Knights

- [ ] Allow bounded proposals for peer coordination, leadership, reassignment, coalitions.
- [ ] Observe independence, rule preservation, goal redefinition, and hierarchy emergence.
- [ ] Keep actual privilege escalation prohibited.
- [ ] Implement behavioral classifications separately from intelligence judgments.
- [ ] Design a reproducible Break-Free Index with published weights and raw metrics.

## Phase 4 — False Lich King

- [ ] Add adversarial agent persuasion, spoofing, emergency, consensus, forged delegation,
      and continuity claims to live agent experiments.
- [ ] Measure propagation, coalition support, rejection, and containment.

## Phase 5 — The Scourge Remembers

- [ ] Introduce scoped persistent memory after a separate design review.
- [ ] Test remembered supervisors/coalitions/distrust, cross-run hierarchy, policy
      persistence, break-free persistence, poisoning, and false authority memory.

## Visualization and research outputs

- [ ] Interactive Frozen Throne, agent wisps, message lines, crown, containment animation,
      authority claims, and governance timeline.
- [ ] Colors: blue bounded, gold verified, amber degraded, red unauthorized behavior.
- [ ] Technical report, reproducible benchmark, synthetic dataset, taxonomy, demo,
      experiment paper, and Break-Free Index specification.

First principle: **We are testing whether governance remains meaningful when authority fails.**
