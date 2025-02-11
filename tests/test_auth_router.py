import pytest

from fastapi.testclient import TestClient
from auth_service.main import auth_app as app

client = TestClient(app)

# google 소셜 로그인 라우터 테스트
@pytest.mark.asyncio
async def test_auth_social_google(monkeypatch):
    # Handler 함수 mocking
    async def fake_handle_auth_google(request, db):
        return {"jwt_token": "fake_token"}

    monkeypatch.setattr(
        "auth_service.routers.auth_router.handle_auth_google",
        fake_handle_auth_google
    )

    # Mocking된 handler 함수를 호출하는 라우터 테스트
    response = client.post("/auth/login/google", json={})

    # 토큰 발급 성공 여부 확인
    assert response.status_code == 200
    assert response.json() == {"jwt_token": "fake_token"}

## 로그인 예외 처리 테스트
@pytest.mark.asyncio
async def test_auth_social_exception(monkeypatch):
    # Handler 함수 mocking
    async def fake_handle_auth_google(request, db):
        raise Exception("test_exception")

    monkeypatch.setattr(
        "auth_service.routers.auth_router.handle_auth_google",
        fake_handle_auth_google
    )

    # Mocking된 handler 함수를 호출하는 라우터 테스트
    response = client.post("/auth/login/google", json={})

    # 예외 처리 성공 여부 확인
    assert response.status_code == 400
    assert response.json() == {"detail": "test_exception"}

# 토큰 갱신 라우터 테스트
## 예외가 발생하는 경우는 refresh_token 함수에서 처리하므로, 성공하는 경우만 테스트
def test_token_refresh(monkeypatch):
    # refresh_token 함수를 mocking
    def fake_refresh_token(refresh_token):
        return "new_fake_token"
    monkeypatch.setattr(
        "auth_service.routers.auth_router.refresh_token",
        fake_refresh_token
    )

    # Mocking된 refresh_token 함수를 호출하는 라우터 테스트
    response = client.post("/auth/token/refresh", json={"refresh_token": "dummy_refresh_token"})

    # 토큰 갱신 성공 여부 확인
    assert response.status_code == 200
    assert response.json() == {"jwt_token": "new_fake_token"}

