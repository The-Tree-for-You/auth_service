from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError
from typing import Any, Dict

from auth_service.core.config import OAUTH_GOOGLE_CONFIG
from auth_service.core.database import get_db
from auth_service.models.auth_model import User
from auth_service.handlers.token_handler import create_access_token, create_refresh_token

# OAuth 클라이언트 설정
oauth = OAuth()
oauth.register(
    name="google",
    client_id=OAUTH_GOOGLE_CONFIG["client_id"],
    client_secret=OAUTH_GOOGLE_CONFIG["client_secret"],
)

# Google OAuth
async def handle_auth_google(request: Request, db: Session) -> Dict[str, Any]:
    try:
        # Google에서 access token 발급
        token = await request.app.state.oauth.google.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth 에러: {error.error}"
        )
    
    # Google API를 통해 사용자 정보 조회
    response = await request.app.state.oauth.google.get("userinfo", token=token)
    user_info = response.json()

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

    # 로그인 후 토큰 발급
    jwt_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return {
        "jwt_token": jwt_token,
        "refresh_token": refresh_token,
        "user": {
            "email": user.email,
            "name": user.name
        }
    }