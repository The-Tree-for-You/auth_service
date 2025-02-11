from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from auth_service.core.database import get_db
from auth_service.handlers.google_social_handler import handle_auth_google
from auth_service.handlers.token_handler import refresh_token

router = APIRouter()

# 소셜 로그인 라우터
@router.post(path="/login/{provider}", description="소셜 로그인 / 회원가입")
async def auth_social(provider: str, request: Request, db: Session = Depends(get_db)):

    # provier에 따라 로직 분기
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider is required"
        )
    
    try:
        # Stateless를 위해 handler에서 JWT을 발급 후 반환
        if provider == "google":
            result = await handle_auth_google(request, db)
            return JSONResponse(
                content=result,
                status_code=status.HTTP_200_OK
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 토큰 갱신 클래스
class TokenRefreshRequest(BaseModel):
    refresh_token: str

# 토큰 갱신 라우터
@router.post(path="/token/refresh")
async def token_refresh(request: Request, token_request: TokenRefreshRequest, db: Session = Depends(get_db)):
    new_jmt_token = refresh_token(token_request.refresh_token)

    return JSONResponse(
        content={"jwt_token": new_jmt_token},
        status_code=status.HTTP_200_OK
    )