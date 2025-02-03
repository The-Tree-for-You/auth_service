from pydantic import BaseModel, EmailStr
from typing import Optional

# 클라이언트로부터 받을 데이터를 정의하는 클래스
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

# 소셜 로그인으로 신규 가입할 때 사용할 클래스
class UserCreate(UserBase):
    social_provider: str
    social_id: str

# 사용자 정보 응답 클래스
class UserResponse(UserBase):
    id: int
    social_provider: str

    class Config:
        orm_mode = True