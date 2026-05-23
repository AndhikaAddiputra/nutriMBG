from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

TUNNEL_URL_FILE = Path(__file__).resolve().parents[3] / "backend" / "tunnel_url.txt"


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/api/v1/public-url")
def public_url() -> dict:
    url = ""
    if TUNNEL_URL_FILE.exists():
        url = TUNNEL_URL_FILE.read_text().strip()
    return {"url": url, "backend": "running"}
