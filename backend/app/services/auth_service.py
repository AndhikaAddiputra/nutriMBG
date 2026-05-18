from typing import Dict, Any, Union
from schemas.auth_schemas import LoginRequest, CoordinatorProfile, AdminProfile, RoleEnum

class AuthError(Exception):
    """Exception dasar untuk autentikasi."""
    pass

class RoleMismatchError(AuthError):
    """Exception khusus jika kredensial benar tapi role yang direquest tidak cocok."""
    pass

class InvalidCredentialsError(AuthError):
    """Exception jika email atau password salah."""
    pass

# --- MOCK DATABASE (Ganti dengan SQLAlchemy query di production) ---
MOCK_USERS = {
    "koor@nutrimbg.go.id": {
        "id": 101,
        "name": "Budi Koordinator",
        "email": "koor@nutrimbg.go.id",
        # Hash dari 'koor123'
        "hashed_password": "$2b$12$KkK.q3XG/wR/jA7j4OQ3rOQG1L9v/7xV2P3G/U6t.M2eN7/wR/jA", 
        "role": "koordinator",
        "province": "Jawa Barat",
        "district": "Kota Bandung",
        "district_id": "JB-01",
        "default_education_level": "SD"
    },
    "admin@nutrimbg.go.id": {
        "id": 1,
        "name": "Sistem Admin",
        "email": "admin@nutrimbg.go.id",
        # Hash dari 'admin123'
        "hashed_password": "$2b$12$KkK.q3XG/wR/jA7j4OQ3rOQG1L9v/7xV2P3G/U6t.M2eN7/wR/jA",
        "role": "administrator"
    }
}

def get_managed_provinces_for_admin(admin_id: int) -> list:
    return ["Jawa Barat", "Jawa Tengah"]

def build_user_profile(user_db: Dict[str, Any]) -> Union[CoordinatorProfile, AdminProfile]:
    if user_db["role"] == "koordinator":
        return CoordinatorProfile(
            id=user_db["id"],
            name=user_db["name"],
            email=user_db["email"],
            role=RoleEnum.koordinator,
            province=user_db.get("province", ""),
            district=user_db.get("district", ""),
            default_education_level=user_db.get("default_education_level", "SD")
        )
    elif user_db["role"] == "administrator":
        provinces = get_managed_provinces_for_admin(user_db["id"])
        return AdminProfile(
            id=user_db["id"],
            name=user_db["name"],
            email=user_db["email"],
            role=RoleEnum.administrator,
            managed_provinces=provinces
        )

def authenticate_user(login_data: LoginRequest) -> tuple[Dict[str, Any], Union[CoordinatorProfile, AdminProfile]]:
    from core.security import verify_password
    
    user = MOCK_USERS.get(login_data.email)
    
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise InvalidCredentialsError("Email atau kata sandi tidak valid.")
        
    if user["role"] != login_data.role:
        raise RoleMismatchError("Peran tidak sesuai. Silakan pilih peran yang benar.")
        
    profile = build_user_profile(user)
    
    return user, profile