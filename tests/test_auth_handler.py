import pytest

from fastapi.testclient import TestClient

from auth_service.main import auth_app as app
from auth_service.handlers.google_social_handler import handle_auth_google
from auth_service.models.auth_model import User

client = TestClient(app)

# 테스트 환경 설정
## 테스트용 환경변수
@pytest.fixture(autouse=True)
def setup(monkeypatch):
    # 테스트용 환경변수 설정
    monkeypatch.setenv("OAUTH_GOOGLE_CONFIG", {
        "client_id": "dummy_client_id",
        "client_secret": "dummy_client_secret"
    })
    monkeypatch.setattr("auth_service.handlers.google_social_handler.OAUTH_GOOGLE_CONFIG", {
        "client_id": "dummy_client_id",
        "client_secret": "dummy_client_secret"
    })

## dummy_data - 비동기 함수에서 사용할 수 없어서 함수로 변경
### Fake google token 발급 함수
async def fake_authorize_access_token(request):
    return "dummy_token"

### Fake google 사용자 정보 조회 함수 - 정상 사용자 정보
async def fake_get(url, token):
    class FakeResponse:
        def json(self):
            return {"id": "dummy_id", "email": "dummy_email", "name": "dummy_name"}
    return FakeResponse()

### Fake google 사용자 정보 조회 함수 - 이메일 정보 없음
async def fake_get_no_email(url, token):
    class FakeResponse:
        def json(self):
            return {"id": "dummy_id", "name": "dummy_name"}
    return FakeResponse()

## 테스트용 DB 세션
class FaskeDBSession:
    def __init__(self, user_exists=False):
        self.user_exists = user_exists
        self.added_users = [] # 추가된 사용자 저장용
    
    def query(self, model):
        # 모의 쿼리 클래스
        class FakeQuery:
            def __init__(self, user_exists):
                self.user_exists = user_exists

            def filter(self, *args, **kwargs):
                return self
            
            def first(self):
                # 기존 사용자가 있는 경우
                if self.user_exists:
                    return User(email="dummy_email", name="dummy_name")
                # 기존 사용자가 없는 경우
                else:
                    return None
        return FakeQuery(self.user_exists)
    
    def add(self, user):
        self.added_users.append(user)
    
    def commit(self):
        pass

    def refresh(self, user):
        pass
            
## 테스트용 Request 객체
class FakeRequest:
    pass

## 테스트용 JWT 토큰 발급 함수
@pytest.fixture(autouse=True)
def mock_token(monkeypatch):
    def fake_create_access_token(data):
        return "fake_token"
    
    def fake_create_refresh_token(data):
        return "fake_refresh_token"
    
    monkeypatch.setattr("auth_service.handlers.google_social_handler.create_access_token", fake_create_access_token)
    monkeypatch.setattr("auth_service.handlers.google_social_handler.create_refresh_token", fake_create_refresh_token)

# Google 로그인 테스트
## 기존 사용자 로그인
@pytest.mark.asyncio
async def test_handle_auth_google():
    # 테스트용 Request mocking
    fake_request = FakeRequest()
    fake_request.app = type(
        'FakeApp',
        (),
        {"state": type(
            'FakeState',
            (),
            {"oauth": type(
                'FakeOAuth',
                (),
                {"google": type(
                    'FakeGoogle',
                    (),
                    {"authorize_access_token": fake_authorize_access_token,
                     "get": fake_get
                    })
                }
            )}
        )}
    )

    # 테스트용 DB 세션 - 기존 사용자가 있는 경우
    db = FaskeDBSession(user_exists=True)

    # 테스트용 로직 실행
    result = await handle_auth_google(fake_request, db)

    # 결과 검증
    assert "jwt_token" in result
    assert "refresh_token" in result
    assert result["user"]["email"] == "dummy_email"
    assert result["user"]["name"] == "dummy_name"

## 새로운 사용자 로그인
@pytest.mark.asyncio
async def test_handle_auth_google_new_user():
    # 테스트용 Request mocking
    fake_request = FakeRequest()
    fake_request.app = type(
        'FakeApp',
        (),
        {"state": type(
            'FakeState',
            (),
            {"oauth": type(
                'FakeOAuth',
                (),
                {"google": type(
                    'FakeGoogle',
                    (),
                    {"authorize_access_token": fake_authorize_access_token,
                     "get": fake_get
                    })
                }
            )}
        )}
    )
    # 테스트용 DB 세션 - 기존 사용자가 없는 경우
    db = FaskeDBSession()

    # 테스트용 로직 실행
    result = await handle_auth_google(fake_request, db)

    # 결과 검증
    assert "jwt_token" in result
    assert "refresh_token" in result
    assert result["user"]["email"] == "dummy_email"
    assert result["user"]["name"] == "dummy_name"

## Google 계정에 이메일 정보가 없는 경우
@pytest.mark.asyncio
async def test_handle_auth_google_no_email():
    # 테스트용 Request mocking
    fake_request = FakeRequest()
    fake_request.app = type(
        'FakeApp',
        (),
        {"state": type(
            'FakeState',
            (),
            {"oauth": type(
                'FakeOAuth',
                (),
                {"google": type(
                    'FakeGoogle',
                    (),
                    {"authorize_access_token": fake_authorize_access_token,
                     "get": fake_get_no_email
                    })
                }
            )}
        )}
    )

    # 테스트용 DB 세션
    db = FaskeDBSession()

    # 테스트용 로직 실행
    with pytest.raises(Exception):
        await handle_auth_google(fake_request, db)