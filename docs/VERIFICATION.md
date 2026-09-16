# Phase 0 verification

Verified locally on 2026-09-16 with Python 3.13.7 on Windows.

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -v` | 32 tests passed, including parameterized identity/claim cases, the 70-cell role/action matrix, and 25 state-transition pairs. |
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
