import json
from typing import Any


def extract_json_payload(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    start_candidates = [idx for idx in (cleaned.find("["), cleaned.find("{")) if idx != -1]
    if not start_candidates:
        raise ValueError("Response does not contain JSON payload.")
    start = min(start_candidates)

    end_candidates = [idx for idx in (cleaned.rfind("]"), cleaned.rfind("}")) if idx != -1]
    if not end_candidates:
        raise ValueError("Response does not contain JSON payload.")
    end = max(end_candidates)

    snippet = cleaned[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to decode JSON payload: {exc.msg}") from exc
