from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="coordinator", pattern="^(coordinator|admin)$")
    province: str = Field(min_length=1, max_length=100)
    kabupaten: str = Field(min_length=1, max_length=100)
    default_education_level: str = Field(default="SMP", pattern="^(SD_1_3|SD_4_6|SMP|SMA)$")


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    province: str
    kabupaten: str
    default_education_level: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
