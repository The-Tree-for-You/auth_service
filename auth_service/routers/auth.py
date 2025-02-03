import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError

from core.config import OAUTH_GOOGLE_CONFIG
from core.database import get_db
from core.security import create_access_token, create_refresh_token, verify_refresh_token
from models.auth_model import User

router = APIRouter()

# OAuth 클라이언트 설정
oauth = OAuth()
oauth.register(
    name="google",
    client_id=OAUTH_GOOGLE_CONFIG["client_id"],
    client_secret=OAUTH_GOOGLE_CONFIG["client_secret"],
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs=OAUTH_GOOGLE_CONFIG['scope']
)

@router.get("/login/google")
async def login_google(request: Request):
    """
    사용자를 Google 로그인 페이지로 리다이렉트
    """
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback", name="auth_google_callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google 로그인 callback 엔드포인트
    Google에서 access token을 받서 사용자 정보를 조회한 뒤, DB에 사용자가 존재하는지 확인하고 없으면 신규 생성합니다.
    """
    try:
        # Google에서 access token 발급
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth 에러: {error.error}"
        )
    
    # Google API를 통해 사용자 정보 조회
    resp = await oauth.google.get("userinfo", token=token)
    user_info = resp.json()

    # user_info 예시: { "id": "google-id", "email": "user@example.com", "name": "User Name" }
    if not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google 계정에 이메일 정보가 없습니다."
        )
    
    google_id = user_info["id"]
    email = user_info["email"]
    name = user_info["name"]

    # DB에서 이미 Google 계정으로 가입한 사용자 조회
    user = db.query(User).filter(
        User.social_id == google_id,
        User.social_provider == "google"
    ).first()

    # 사용자가 존재하지 않으면 신규 생성
    if not user:
        user = User(
            email=email,
            name=name,
            social_provider="google",
            social_id=google_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 로그인 성공 후 인증을 위한 jmt 토큰 발급 및 반환
    jmt_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    return {
        "jmt_token": jmt_token,
        "refresh_token": refresh_token,
        "user": {
            "email": user.email,
            "name": user.name
        }
    }


# 토큰 갱신 요청 클래스
class TokenRefreshRequest(BaseModel):
    refresh_token: str

@router.post("/token/refresh")
async def token_refresh(request: Request, token_request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    "refresh_token"을 이용해 새로운 jmt_token을 발급
    """
    payload = verify_refresh_token(token_request.refresh_token)
    
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_jmt_token = create_access_token({"sub": user.email})
    return {"jmt_token": new_jmt_token}