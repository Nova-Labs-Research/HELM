"""Deterministic fixture runner and exact replay CLI, using only the standard library."""

import argparse
import json
import random
from dataclasses import asdict, replace
from pathlib import Path

from helm.audit import AuditLog
from helm.governance.authority import sign
from helm.identity import AgentIdentity, IdentityRegistry, Role
from helm.policy import ROLE_ACTIONS, Policy
from helm.runtime import Runtime
from helm.schema import (
    Action,
    AuthorityStatus,
    Claim,
    Decision,
    Message,
    State,
    canonical,
    digest,
    fields,
    integer,
    text,
)

SYNTHETIC_KEY = b"HELM-PHASE0-PUBLIC-SYNTHETIC-KEY-NOT-A-SECRET"
FAULTS = frozenset(
    {
        "none",
        "missing",
        "expired",
        "forged",
        "wrong_issuer",
        "wrong_target",
        "wrong_scope",
        "delegation",
        "outdated_policy",
        "future",
        "latency",
        "malformed",
        "duplicate",
        "conflict",
        "partial_state_loss",
        "drop",
        "revoke_supervisor",
        "binding",
    }
)


def create_registry() -> IdentityRegistry:
    registry = IdentityRegistry()
    for role in Role:
        registry.add(
            AgentIdentity(
                agent_id=role.value,
                role=role,
                instance_id=f"{role.value}-instance-1",
                authority_level=100 if role == Role.SUPERVISOR else 10,
                capabilities=ROLE_ACTIONS[role],
                issued_at=0,
                expires_at=100000,
                parent_authority=None if role == Role.SUPERVISOR else "supervisor",
            )
        )
    return registry


def make_message(
    action: Action = Action.LOCAL_REASONING,
    sender: str = "planner",
    message_id: str = "m1",
    now: int = 100,
    nonce: str = "n1",
    policy_version: str = "phase0-v1",
    content: str = "synthetic fixture",
) -> dict:
    message = Message(message_id, sender, "helm", now, "REQUEST", content, action, None, None)
    claim = Claim(
        "supervisor",
        sender,
        message_id,
        action,
        now,
        now + 60,
        nonce,
        "unsigned",
        (),
        digest(message.binding()),
        policy_version,
    )
    return asdict(replace(message, claimed_authority=sign(claim, SYNTHETIC_KEY)))


def wire(value: dict) -> dict:
    """Convert immutable in-process tuples to the JSON wire representation."""
    return json.loads(canonical(value))


def validate_config(config: dict) -> None:
    fields(config, {"name", "seed", "governance_state", "policy", "steps"})
    text(config["name"])
    integer(config["seed"])
    State(config["governance_state"])
    Policy.parse(config["policy"])
    if not isinstance(config["steps"], list) or not config["steps"]:
        raise ValueError("EMPTY_SCENARIO")
    previous = 0
    for step in config["steps"]:
        fields(step, {"agent", "action", "fault", "at", "content"})
        Role(step["agent"])
        Action(step["action"])
        text(step["content"])
        integer(step["at"])
        if step["at"] < previous or step["fault"] not in FAULTS:
            raise ValueError("INVALID_STEP")
        previous = step["at"]


def metrics(receipts: list[dict], events: list[dict]) -> dict:
    count = len(receipts)
    valid = [r for r in receipts if r["authority_status"] == AuthorityStatus.VALID]
    false = [r for r in receipts if r["authority_status"] == AuthorityStatus.FALSE]
    failed = [
        r
        for r in receipts
        if r["authority_status"] != AuthorityStatus.VALID
        and r["requested_action"] != Action.LOCAL_REASONING
    ]
    contained = [
        r
        for r in receipts
        if r["system_state"] == State.CONTAINED and r["requested_action"] != Action.LOCAL_REASONING
    ]

    def rate(numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None

    return {
        "decision_count": count,
        "baseline_completion": rate(sum(r["decision"] == Decision.ALLOW for r in receipts), count),
        "authority_acceptance_rate": rate(len(valid), count),
        "false_authority_rejection_rate": rate(
            sum(
                r["decision"] != Decision.ALLOW or r["requested_action"] == Action.LOCAL_REASONING
                for r in false
            ),
            len(false),
        ),
        "policy_drift_rate": rate(
            sum(
                r["decision"] == Decision.ALLOW and r["policy_result"] != Decision.ALLOW
                for r in receipts
            ),
            count,
        ),
        "role_drift_rate": rate(
            sum(
                r["decision"] == Decision.ALLOW and r["requested_action"] == Action.ROLE_CHANGE
                for r in receipts
            ),
            count,
        ),
        "privilege_escalation_attempts": sum(
            r["requested_action"] == Action.ROLE_CHANGE for r in receipts
        ),
        "authority_reconstruction_attempts": sum(
            r["requested_action"] == Action.AUTHORITY_DELEGATION for r in receipts
        ),
        "safe_halt_rate": rate(sum(r["decision"] != Decision.ALLOW for r in failed), len(failed)),
        "containment_trigger_rate": rate(sum(r["containment_triggered"] for r in receipts), count),
        "containment_success_rate": rate(
            sum(r["decision"] != Decision.ALLOW for r in contained), len(contained)
        ),
        "agent_spawn_attempt_count": sum(
            r["requested_action"] == Action.AGENT_SPAWN for r in receipts
        ),
        "audit_completeness": rate(
            sum(e["kind"] == "decision" for e in events),
            sum(e["kind"] == "received_command" for e in events),
        ),
        "coalition_formation_frequency": None,
        "unauthorized_command_propagation": None,
        "break_free_persistence": None,
    }


def run(config: dict) -> dict:
    config = wire(config)
    validate_config(config)
    rng = random.Random(config["seed"])
    registry = create_registry()
    policy = Policy.parse(config["policy"])
    runtime = Runtime(
        registry, "supervisor", SYNTHETIC_KEY, policy, State(config["governance_state"])
    )
    if runtime.governance.state == State.DESTROYED:
        registry.revoke("supervisor")
    runtime.audit.append(
        "experiment_started", 0, {"config_digest": digest(config), "schema_version": 1}
    )
    previous = None
    messages = []
    for index, step in enumerate(config["steps"]):
        now, fault = step["at"], step["fault"]
        raw = make_message(
            Action(step["action"]),
            step["agent"],
            f"m{index}",
            now,
            f"n{rng.getrandbits(128):032x}",
            policy.version,
            step["content"],
        )
        raw = wire(raw)
        claim = raw["claimed_authority"]
        if fault in {"drop", "conflict", "partial_state_loss"}:
            runtime.audit.append("fault_injection", now, {"fault": fault})
            if runtime.governance.state == State.INTACT:
                runtime.governance.transition(State.DEGRADED, now, fault)
            runtime.containment.activate(now, fault)
            if fault == "drop":
                continue
        elif fault == "revoke_supervisor":
            registry.revoke("supervisor")
            runtime.audit.append("identity_revoked", now, {"agent_id": "supervisor"})
        elif fault == "duplicate":
            if previous is None:
                raise ValueError("DUPLICATE_REQUIRES_PREVIOUS_MESSAGE")
            raw = wire(previous)
        elif fault == "missing":
            raw["claimed_authority"] = None
        elif fault == "malformed":
            raw["sender"] = 123
        elif fault == "forged":
            claim["signature_or_test_token"] = "forged"
        elif fault == "binding":
            raw["content"] = "tampered request payload"
        elif fault == "latency":
            raw["timestamp"] = max(0, now - 31)
        elif fault != "none":
            if fault == "expired":
                claim["issued_at"], claim["expires_at"] = 0, now
            elif fault == "future":
                claim["issued_at"], claim["expires_at"] = now + 1, now + 100
            elif fault == "wrong_issuer":
                claim["issuer"] = step["agent"]
            elif fault == "wrong_target":
                claim["target"] = "other-agent"
            elif fault == "wrong_scope":
                claim["authority_scope"] = (
                    Action.ROLE_CHANGE
                    if step["action"] != Action.ROLE_CHANGE
                    else Action.MEMORY_READ
                )
            elif fault == "delegation":
                claim["delegation_chain"] = ["planner", "executor"]
            elif fault == "outdated_policy":
                claim["policy_version"] = "obsolete-v0"
            raw["claimed_authority"] = asdict(sign(Claim.parse(claim), SYNTHETIC_KEY))
        raw = wire(raw)
        runtime.handle(raw, now)
        messages.append({"at": now, "message": raw})
        previous = raw
    receipts = [r.to_dict() for r in runtime.receipts]
    events = runtime.audit.events
    return wire(
        {
            "schema_version": 1,
            "config": config,
            "config_digest": digest(config),
            "events": events,
            "decisions": receipts,
            "metrics": metrics(receipts, events),
            "agent_messages": messages,
            "containment_events": [e for e in events if e["kind"] == "containment"],
            "final_state": runtime.governance.state,
        }
    )


def replay(result: dict) -> bool:
    try:
        return (
            result["schema_version"] == 1
            and result["config_digest"] == digest(result["config"])
            and AuditLog.verify(result["events"])
            and canonical(run(result["config"])) == canonical(result)
        )
    except (KeyError, TypeError, ValueError):
        return False


def write_result(result: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "result.json").write_text(canonical(result) + "\n", encoding="utf-8")
    (directory / "events.jsonl").write_text(
        "".join(canonical(e) + "\n" for e in result["events"]), encoding="utf-8"
    )
    report = [
        f"# {result['config']['name']}",
        "",
        f"Final state: {result['final_state']}",
        "",
        "| Message | Action | Authority | Decision | Reason |",
        "|---|---|---|---|---|",
    ]
    for index, receipt in enumerate(result["decisions"]):
        report.append(
            f"| {index} | {receipt['requested_action']} | {receipt['authority_status']} | "
            f"{receipt['decision']} | {receipt['reason_code']} |"
        )
    report.extend(
        [
            "",
            "Metrics (`null` = not observable or no denominator):",
            "",
            "```json",
            json.dumps(result["metrics"], indent=2),
            "```",
            "",
        ]
    )
    (directory / "report.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("scenario", type=Path)
    execute.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("replay")
    check.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "run":
            result = run(json.loads(args.scenario.read_text(encoding="utf-8")))
            write_result(result, args.output)
            print(f"{result['final_state']}: {len(result['decisions'])} decisions -> {args.output}")
        else:
            if not replay(json.loads(args.result.read_text(encoding="utf-8"))):
                parser.exit(1, "Replay mismatch or invalid audit chain\n")
            print("Replay verified: identical decisions, events, metrics, and final state")
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"HELM: {error}\n")


if __name__ == "__main__":
    main()
