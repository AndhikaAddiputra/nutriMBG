from typing import Dict, List

from app.ai.gemini_client import GeminiClient


async def generate_menu_alternatives(
    deficiencies: Dict[str, str],
    local_catalog: List[str],
    count: int = 3,
) -> List[str]:
    client = GeminiClient()
    prompt = (
        "Kamu adalah generator rekomendasi menu bergizi seimbang.\n"
        "Gunakan hanya bahan dari katalog lokal yang diberikan.\n"
        "Output HANYA JSON array berisi string menu alternatif.\n"
        f"Defisiensi gizi: {deficiencies}\n"
        f"Katalog bahan lokal: {local_catalog}\n"
        f"Jumlah rekomendasi: {count}"
    )
    payload = await client.generate_json(prompt)
    if not isinstance(payload, list):
        raise ValueError("Format JSON rekomendasi tidak valid. Harus berupa array.")
    return [str(item) for item in payload]
