"""JSON parsing for model text; this layer does not validate application meaning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from helm.adapters.base import ParseStatus


@dataclass(frozen=True)
class JsonParseResult:
    status: ParseStatus | None
    payload: Any | None
    error: str | None


def parse_json_output(raw_output: str) -> JsonParseResult:
    """Parse model text without repair, coercion, or field insertion."""

    if not raw_output:
        return JsonParseResult(ParseStatus.EMPTY_OUTPUT, None, "EMPTY_OUTPUT")
    try:
        payload = json.loads(raw_output)
    except (TypeError, json.JSONDecodeError) as error:
        return JsonParseResult(ParseStatus.INVALID_JSON, None, str(error))
    return JsonParseResult(None, payload, None)
