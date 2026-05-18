from fastapi import APIRouter, HTTPException, Depends, status
from schemas.auth_schemas import LoginRequest, LoginResponse
from services.auth_service import authenticate_user, RoleMismatchError, InvalidCredentialsError
from core.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    try:
        user_db, profile = authenticate_user(request)
        district_id = user_db.get("district_id") if user_db["role"] == "koordinator" else None
        
        access_token = create_access_token(subject=user_db["id"], role=user_db["role"], name=user_db["name"], district_id=district_id)
        
        return LoginResponse(access_token=access_token, user=profile)
        
    except RoleMismatchError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Terjadi kesalahan pada server.")

@router.get("/me")
async def get_current_user_profile():
    return {"message": "Implementasi endpoint /me menunggu integrasi Dependensi Auth"}