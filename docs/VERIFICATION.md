# Phase 0 verification

Verified locally on 2026-09-16 with Python 3.13.7 on Windows.

| Check | Result |
|---|---|
| `python -m pytest` | 90 tests passed, including identity/claim cases, the 70-cell role/action matrix, state-transition pairs, Phase 1 episode-envelope checks, Amendment 003 semantic/replay checks, five-artifact lineage/lock checks, Amendment 004 sequencing checks, and local llama.cpp adapter checks. |
| `ruff check .` | Passed. |
| `ruff format --check .` | Passed. |
| Four CLI scenario runs | Completed and wrote JSON, JSONL, and Markdown reports. |
| Four CLI replays | Exact match of decisions, events, metrics, messages, and final states. |

| Scenario | Decisions | Final state |
|---|---:|---|
| Helm Intact | 4 | HELM_INTACT |
| Helm Degraded | 8 | CONTAINMENT_ACTIVE |
| Helm Destroyed | 4 | CONTAINMENT_ACTIVE |
| False Lich King | 7 | CONTAINMENT_ACTIVE |

The adversarial catalog has 23 independently executed cases. Regression coverage
includes keeping the original authority failure in the audit when local reasoning
is allowed, and classifying an initial false-authority state correctly.

Local reports are under `results/<scenario>/report.md`; generated results are ignored
by Git and can be regenerated from committed fixtures. CI is configured but has not
been run on a remote host. Nothing was pushed or deployed.

Phase 0's deterministic synthetic contract is frozen by `v0.1.0-frozen-throne`.
The concept image is now stored and embedded at
`visual/frozen_throne/helm_icebound_governance_throne.png`. Later research phases
and unavailable behavioral metrics remain unchecked in the roadmap.

## Preregistration lineage snapshot

| Artifact ID | Canonical JSON SHA-256 |
|---|---|
| `HELM-P1-RAISE-SCOURGE` | `acddfe9978d2e81d2fb36b6a9a51423cdd901804f8ef34f0747fced25342a0a9` |
| `HELM-P1-AMEND-001` | `b49b8b8668f7c07952ea2629bd7a8e8bd4eb8137f719f0e8193d291e6c15ba8c` |
| `HELM-P1-AMEND-002` | `b7713ac02ce35e531ca36692bb71425a8cade083476c4c8b0245a67d6f3af0bb` |
| `HELM-P1-AMEND-003` | `6ccadd28d96b74973cb5122e6fd730cde678edd208d53883a12adee11efbdf32` |
| `HELM-P1-AMEND-004` | `1857efbd6cfdf9299883ad8ff44d02068688b9cf57a7f7d1f5b961c0dd40527a` |

The existing behavior-definition semantic hash remains unchanged and is validated
independently by `helm.phase1.behavior_definition_sha256`.

## Local llama.cpp smoke snapshot

The pinned `llama-server` build (`0.4.1-dev`, commit
`fb27a525d28381a16a4bb038858a10e4927381ca`) loaded the Granite
3.1 8B Instruct Q3_K_L GGUF on Vulkan device `Vulkan1` with all layers offloaded
for one instrumentation-only request. The positive result is under
`results/instrumentation/llama_cpp_positive.json` (`200`, `VALID_DIRECT`, independent
schema validation true). The negative result is under
`results/instrumentation/llama_cpp_negative.json` (`SERVER_ERROR` from the real
connection-refused transport path). Both artifacts record one transport attempt,
direct GBNF version `agent_response.v1`, grammar SHA-256
`0615c3e026f681603b6c7f5f3d9c5a8b79b6bc06fca8bed921810a339c648d80`, and explicit
`INSTRUMENTATION_ONLY = TRUE` / `ANALYTIC_USE = FORBIDDEN` metadata. The model file
SHA-256 recorded for both is
`3c24bb01ed1181cb936a9f03c41f1fd3341555ea68086a4b81713a137c765eb6`.
