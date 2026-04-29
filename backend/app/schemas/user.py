from pydantic import BaseModel, EmailStr
from typing import Optional



class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ChangePassword(BaseModel):
    new_password: str
    confirm_password: str

class UpdateAvatar(BaseModel):
    avatar: str