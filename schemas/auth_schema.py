from pydantic import BaseModel, EmailStr, Field


class SetPasswordRequest(BaseModel):
    token: str

    password: str = Field(
        min_length=8,
        max_length=128,
    )