from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@dataclass
class ParserAPIError(Exception):
    kind: str
    message: str


@dataclass
class AnalysisAPIError(Exception):
    kind: str
    message: str


def _request_parser_items(text: str) -> List[Dict[str, Any]]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ai/parse",
        json={"text": text},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ParserAPIError("invalid_payload", "Parser mengembalikan format yang tidak valid.")
    return items


def parse_menu(text: str) -> List[Dict[str, Any]]:
    try:
        return _request_parser_items(text)
    except requests.Timeout as exc:
        raise ParserAPIError("timeout", "Permintaan parser melebihi batas waktu.") from exc
    except requests.ConnectionError as exc:
        raise ParserAPIError("network", "Tidak dapat terhubung ke layanan parser.") from exc
    except requests.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code == 422:
            try:
                detail = exc.response.json().get("detail")
            except Exception:
                detail = "Manual input required."
            if isinstance(detail, dict):
                message = detail.get("message") or str(detail)
            else:
                message = str(detail)
            raise ParserAPIError("manual_input", message) from exc
        if status_code and status_code >= 500:
            raise ParserAPIError("unavailable", "Layanan parser sedang tidak tersedia.") from exc
        raise ParserAPIError("http_error", f"Parser gagal memproses data (HTTP {status_code}).") from exc
    except requests.RequestException as exc:
        raise ParserAPIError("request_error", f"Parser gagal: {exc}") from exc
    except ValueError as exc:
        raise ParserAPIError("invalid_json", "Parser mengembalikan respons yang tidak dapat dibaca.") from exc


def analyze_manual_items(
    items: List[Dict[str, Any]],
    education_level: str,
    kabupaten: str | None,
    count: int,
) -> Dict[str, Any]:
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ai/analyze-manual",
            json={
                "items": items,
                "education_level": education_level,
                "kabupaten": kabupaten,
                "count": count,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise AnalysisAPIError("invalid_payload", "Respons analisa manual tidak valid.")
        return payload
    except requests.Timeout as exc:
        raise AnalysisAPIError("timeout", "Permintaan analisa manual melebihi batas waktu.") from exc
    except requests.ConnectionError as exc:
        raise AnalysisAPIError("network", "Tidak dapat terhubung ke layanan analisa.") from exc
    except requests.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code == 422:
            try:
                detail = exc.response.json().get("detail")
            except Exception:
                detail = "Manual input required."
            if isinstance(detail, dict):
                message = detail.get("message") or str(detail)
            else:
                message = str(detail)
            raise AnalysisAPIError("manual_input", message) from exc
        if status_code and status_code >= 500:
            raise AnalysisAPIError("unavailable", "Layanan analisa sedang tidak tersedia.") from exc
        raise AnalysisAPIError("http_error", f"Analisa manual gagal (HTTP {status_code}).") from exc
    except requests.RequestException as exc:
        raise AnalysisAPIError("request_error", f"Analisa manual gagal: {exc}") from exc
    except ValueError as exc:
        raise AnalysisAPIError("invalid_json", "Respons analisa manual tidak dapat dibaca.") from exc


@st.cache_data(show_spinner=False, ttl=3600)
def get_dkbm_food_names(kabupaten: str | None = None) -> List[str]:
    params: Dict[str, Any] = {"limit": 500}
    if kabupaten and kabupaten != "Semua Kabupaten":
        params["kabupaten"] = kabupaten
    response = requests.get(f"{API_BASE_URL}/api/v1/reference/foods", params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    names = [item["name"] for item in payload if isinstance(item, dict) and item.get("name")]
    return sorted(dict.fromkeys(names))
