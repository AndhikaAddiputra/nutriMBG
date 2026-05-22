import requests # Digunakan saat implementasi API asli

class AuthError(Exception):
    """Custom exception untuk error login."""
    pass

def login(email, password, role):
    if role == "koordinator" and email == "koor@nutrimbg.go.id" and password == "koor123":
        return {
            "token": "jwt_koordinator_token_xyz890",
            "user": {"id": 101, "name": "Budi Koordinator", "district": "Kota Bandung"}
        }
    elif role == "administrator" and email == "admin@nutrimbg.go.id" and password == "admin123":
        return {
            "token": "jwt_admin_token_abc123",
            "user": {"id": 1, "name": "Sistem Admin", "district": "Pusat"}
        }
    else:
        raise AuthError("Email, kata sandi salah, atau peran tidak sesuai.")