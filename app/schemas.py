from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class JobCreate(BaseModel):
    title: str
    company:str
    status: str