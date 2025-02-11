from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from auth_service.core.config import JWT_CONFIG

app = FastAPI(title="Auth Service", version="0.1.0")

# OAuth2 토큰 생성
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="login",
    tokenUrl="token"
)

# 토큰 생성 함수
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    # 토큰 만료 시간 설정
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=JWT_CONFIG["access_token_expire_minutes"])
    to_encode.update({
        "exp": expire,
        "token_type": JWT_CONFIG["access_token_type"]
        })

    # JWT 토큰 인코딩
    encoded_jwt = jwt.encode(to_encode, JWT_CONFIG["secret_key"], algorithm=JWT_CONFIG["algorithm"])
    return encoded_jwt

# 갱신 토큰 생성 함수
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    # 토큰 만료 시간 설정
    expire = datetime.now() + timedelta(days=JWT_CONFIG["refresh_token_expire_days"])
    to_encode.update({
        "exp": expire,
        "token_type": JWT_CONFIG["refresh_token_type"]
    })

    # JWT 토큰 인코딩
    encoded_jwt = jwt.encode(to_encode, JWT_CONFIG["secret_key"], algorithm=JWT_CONFIG["algorithm"])
    return encoded_jwt

# 토큰 갱신 함수
def refresh_token(token: str):
    payload = verify_refresh_token(token)
    return create_access_token({"sub": payload.get("sub")})

# 토큰 검증 함수
def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_CONFIG["secret_key"], algorithms=[JWT_CONFIG["algorithm"]])

        token_type = payload.get("token_type")
        if token_type != JWT_CONFIG["access_token_type"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
# refresh token 검증 함수
def verify_refresh_token(token: str):
    try:
        # "refresh token" 검증
        payload = jwt.decode(token, JWT_CONFIG["secret_key"], algorithms=JWT_CONFIG["algorithm"])

        token_type = payload.get("token_type")
        if token_type != JWT_CONFIG["refresh_token_type"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )