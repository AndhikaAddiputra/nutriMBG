from typing import Dict, List
import logging

from app.ai.gemini_client import GeminiClient


class ManualInputRequired(RuntimeError):
    """Raised when automatic parsing cannot proceed and manual input is required."""


async def parse_menu(text: str) -> List[Dict[str, float]]:
    client = GeminiClient()
    prompt = (
        "Kamu adalah parser menu makanan. Ekstrak bahan dan estimasi berat gram.\n"
        "Kembalikan HANYA JSON array berisi objek dengan kunci: name, weight_gram.\n"
        "Jika berat tidak disebutkan, gunakan estimasi porsi standar 100 gram.\n"
        f"Input menu: {text}"
    )
    try:
        payload = await client.generate_json(prompt)
    except RuntimeError as exc:
        logging.warning("Gemini client failed: %s", exc)
        raise ManualInputRequired("Automatic parsing failed due to external AI error; manual input required.") from exc

    if not isinstance(payload, list):
        logging.warning("Gemini returned non-list payload: %r", payload)
        raise ManualInputRequired("Automatic parsing returned unexpected format; manual input required.")

    return payload
