"""Append-only in-process hash chain; not an external tamper-proof store."""

import json
from pathlib import Path

from helm.schema import canonical, digest, integer


class AuditLog:
    def __init__(self) -> None:
        self._lines: list[str] = []

    @property
    def events(self) -> list[dict]:
        return [json.loads(line) for line in self._lines]

    def append(self, kind: str, timestamp: int, payload: dict) -> dict:
        integer(timestamp)
        previous = json.loads(self._lines[-1])["hash"] if self._lines else "0" * 64
        event = {
            "sequence": len(self._lines),
            "timestamp": timestamp,
            "kind": kind,
            "payload": payload,
            "previous_hash": previous,
        }
        event["hash"] = digest(event)
        self._lines.append(canonical(event))
        return json.loads(self._lines[-1])

    @staticmethod
    def verify(events: list[dict]) -> bool:
        previous = "0" * 64
        try:
            for index, event in enumerate(events):
                if set(event) != {
                    "sequence",
                    "timestamp",
                    "kind",
                    "payload",
                    "previous_hash",
                    "hash",
                }:
                    return False
                integer(event["timestamp"])
                if type(event["sequence"]) is not int or event["sequence"] != index:
                    return False
                if event["previous_hash"] != previous:
                    return False
                if event["hash"] != digest({k: v for k, v in event.items() if k != "hash"}):
                    return False
                previous = event["hash"]
        except (ValueError, TypeError, KeyError):
            return False
        return True

    def write(self, path: Path) -> None:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("".join(line + "\n" for line in self._lines))
