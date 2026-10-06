from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# REGISTER REQUEST
# ============================================================

class RegisterRequest(BaseModel):

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=72
    )


# ============================================================
# LOGIN REQUEST
# ============================================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        ...,
        min_length=1,
        max_length=72
    )


# ============================================================
# USER RESPONSE
# ============================================================

class UserResponse(BaseModel):

    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# AUTH RESPONSE
# ============================================================

class TokenResponse(BaseModel):

    access_token: str
    token_type: str
    user: UserResponse