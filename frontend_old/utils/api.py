import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class AuthError(Exception):
    pass


def login(email, password, role):
    url = f"{API_BASE_URL}/api/v1/auth/login"
    try:
        response = requests.post(url, json={"email": email, "password": password}, timeout=10)
    except requests.RequestException as e:
        raise AuthError(f"Gagal terhubung ke server: {e}")

    if response.status_code == 401:
        raise AuthError("Email atau kata sandi salah.")
    if response.status_code != 200:
        raise AuthError(f"Server error: {response.status_code}")

    data = response.json()
    return {
        "token": data["access_token"],
        "user": {
            "id": data["user"]["id"],
            "name": data["user"]["full_name"],
            "district": data["user"]["kabupaten"],
        },
    }
