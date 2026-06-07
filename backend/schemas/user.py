from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut
