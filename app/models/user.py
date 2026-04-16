from pydantic import BaseModel


class UserBase(BaseModel):
    name: str
    email: str
    age: int


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    age: int | None = None


class User(UserBase):
    id: int
