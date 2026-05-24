from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

class ContactCreate(BaseModel):
    name: str
    phone: str