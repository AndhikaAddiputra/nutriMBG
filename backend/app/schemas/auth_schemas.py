from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Union
from enum import Enum

class RoleEnum(str, Enum):
    koordinator = "koordinator"
    administrator = "administrator"

# --- Request Schemas ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: RoleEnum

# --- Profile Schemas ---

class BaseProfile(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleEnum

class CoordinatorProfile(BaseProfile):
    province: str
    district: str
    default_education_level: str

class AdminProfile(BaseProfile):
    managed_provinces: List[str]

# --- Response Schemas ---

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Union[CoordinatorProfile, AdminProfile]