from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    email: str
    username: str
    address: str
    phone: str
    password: str


class Token(BaseModel):
    email: str
    username: str
    access_token: str
    token_type: str