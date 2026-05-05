from typing import Dict, List

from app.ai.gemini_client import GeminiClient


async def parse_menu(text: str) -> List[Dict[str, float]]:
    client = GeminiClient()
    prompt = (
        "Kamu adalah parser menu makanan. Ekstrak bahan dan estimasi berat gram.\n"
        "Kembalikan HANYA JSON array berisi objek dengan kunci: name, weight_gram.\n"
        "Jika berat tidak disebutkan, gunakan estimasi porsi standar 100 gram.\n"
        f"Input menu: {text}"
    )
    payload = await client.generate_json(prompt)
    if not isinstance(payload, list):
        raise ValueError("Format JSON parser tidak valid. Harus berupa array.")
    return payload
