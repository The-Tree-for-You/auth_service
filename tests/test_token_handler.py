import os
import pytest

from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from jose import jwt
from datetime import datetime, timedelta

from auth_service.main import auth_app as app
from auth_service.handlers.token_handler import (
    create_access_token,
    create_refresh_token,
    refresh_token,
    verify_token,
    verify_refresh_token
)

client = TestClient(app)

# 테스트 환경 설정
@pytest.fixture(autouse=True)
def setup(monkeypatch):
    # 테스트용 환경변수 설정
    monkeypatch.setenv("JWT_SECRET_KEY", "dummy_secret_key")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("ACCESS_TOKEN_TYPE", "bearer")
    monkeypatch.setenv("REFRESH_TOKEN_TYPE", "bearer")

    # token_hander의 JWT_CONFIG 값 재정의
    dummy_jwt_config = {
        "secret_key": os.getenv("JWT_SECRET_KEY"),
        "algorithm": os.getenv("JWT_ALGORITHM"),
        "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")),
        "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")),
        "access_token_type": os.getenv("ACCESS_TOKEN_TYPE"),
        "refresh_token_type": os.getenv("REFRESH_TOKEN_TYPE"),
    }
    monkeypatch.setattr("auth_service.handlers.token_handler.JWT_CONFIG", dummy_jwt_config)

# 테스트용 데이터 설정
@pytest.fixture(autouse=True)
def dummy_user_data():
    return {
        "email": "test@example.com",    # 사용자 식별자
        "name": "test_user"
    }

# Access token 발급 테스트
def test_create_access_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    access_token_type = os.getenv("ACCESS_TOKEN_TYPE")

    # 토큰 발급 테스트 코드
    token = create_access_token({"sub": dummy_user_data["email"]})
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])

    assert payload["sub"] == dummy_user_data["email"]
    assert payload["token_type"] == access_token_type

    expiration_delta = datetime.fromtimestamp(payload["exp"]) - (datetime.now() + timedelta(hours=9))   # JWT 토큰은 UTC 기준으로 생성되므로 한국 시간으로 변환
    expectation_delta = timedelta(minutes=access_token_expire_minutes)
    assert abs(expiration_delta - expectation_delta) < timedelta(seconds=1)

# Refresh token 발급 테스트
def test_create_refresh_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")
    refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))
    refresh_token_type = os.getenv("REFRESH_TOKEN_TYPE")

    # 토큰 발급 테스트 코드
    token = create_refresh_token({"sub": dummy_user_data["email"]})
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])

    # 토큰 발급 결과 검증
    assert payload["sub"] == dummy_user_data["email"]
    assert payload["token_type"] == refresh_token_type

    expiration_delta = datetime.fromtimestamp(payload["exp"]) - (datetime.now() + timedelta(hours=9))   # JWT 토큰은 UTC 기준으로 생성되므로 한국 시간으로 변환
    expectation_delta = timedelta(days=refresh_token_expire_days)
    assert abs(expiration_delta - expectation_delta) < timedelta(seconds=1)

# Access token 검증 테스트
## 정상 토큰 검증
def test_verify_access_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_access_token({"sub": dummy_user_data["email"]})

    # 토큰 검증 테스트 코드
    result = verify_token(test_token)

    # 토큰 검증 결과 검증
    assert result["sub"] == dummy_user_data["email"]

## 만료된 토큰 검증
def test_verify_expired_access_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_access_token({"sub": dummy_user_data["email"]}, expires_delta=timedelta(seconds=-1))

    # 토큰 검증 테스트 코드
    try:
        result = verify_token(test_token)
    except HTTPException as e:
        # 토큰 만료로 인한 예외 발생 검증
        assert e.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.detail == "Invaild authentication credentials"

## 토큰 타입 불일치로 인한 검증 실패
def test_verify_invalid_token_type(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_access_token({"sub": dummy_user_data["email"]})

    # 토큰 검증 테스트 코드
    try:
        result = verify_token(test_token.replace("bearer", "Bearer"))
    except HTTPException as e:
        # 토큰 타입 불일치로 인한 예외 발생 검증
        assert e.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.detail == "Invalid token type"

## 사용자 정보 누락으로 인한 검증 실패
def test_verify_invalid_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_access_token({"sub": dummy_user_data["email"]})

    # 토큰 검증 테스트 코드
    try:
        result = verify_token(test_token.replace(dummy_user_data["email"], ""))
    except HTTPException as e:
        # 사용자 정보 누락으로 인한 예외 발생 검증
        assert e.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.detail == "Invalid token"


# Refresh token 검증 테스트
## 정상 토큰 검증
def test_verify_refresh_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_refresh_token({"sub": dummy_user_data["email"]})
    
    # 토큰 검증 테스트 코드
    result = verify_refresh_token(test_token)

    # 토큰 검증 결과 검증
    assert result["sub"] == dummy_user_data["email"]

## 만료된 토큰 검증
def test_verify_expired_refresh_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_refresh_token({"sub": dummy_user_data["email"]}, expires_delta=timedelta(seconds=-1))

    # 토큰 검증 테스트 코드
    try:
        result = verify_refresh_token(test_token)
    except HTTPException as e:
        # 토큰 만료로 인한 예외 발생 검증
        assert e.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.detail == "Invaild refresh token"

## 토큰 타입 불일치로 인한 검증 실패
def test_verify_invalid_refresh_token_type(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_refresh_token({"sub": dummy_user_data["email"]})

    # 토큰 검증 테스트 코드
    try:
        result = verify_refresh_token(test_token.replace("bearer", "Bearer"))
    except HTTPException as e:
        # 토큰 타입 불일치로 인한 예외 발생 검증
        assert e.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.detail == "Invalid token type"

## 사용자 정보 누락으로 인한 검증 실패
def test_verify_invalid_refresh_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 테스트 토큰 발급
    test_token = create_refresh_token({"sub": dummy_user_data["email"]})

    # 토큰 검증 테스트 코드
    try:
        result = verify_refresh_token(test_token.replace(dummy_user_data["email"], ""))
    except HTTPException as e:
        # 사용자 정보 누락으로 인한 예외 발생 검증
        assert e.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.detail == "Invalid refresh token"

# 토큰 갱신 테스트
def test_refresh_token(dummy_user_data):
    # 환경변수 설정
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")

    # 갱신 전 토큰 발급
    original_token = create_refresh_token({"sub": dummy_user_data["email"]})

    # 토큰 갱신 테스트 코드
    new_token = refresh_token(original_token)

    # 토큰 갱신 결과 검증
    assert new_token != original_token
    assert verify_refresh_token(new_token)["sub"] == dummy_user_data["email"]
