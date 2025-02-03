import os

from datetime import datetime, timedelta

# Test 환경 확인
is_TEST_ENV = os.getenv("TEST_ENV", "0")

# DB 설정
DB_CONFIG = {
    "postgresql": {
        "driver": "postgresql",
        "sqlalchemy_url": os.getenv("DATABASE_URL") if not is_TEST_ENV else os.getenv("TEST_DATABASE_URL"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "database": os.getenv("POSTGRES_DB"),
    },
}

# JMT 토큰 설정
JMT_CONFIG = {
    "secret_key": os.getenv("SECRET_KEY"),
    "algorithm": "HS256",
    "access_token_expire_minutes": os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"),
    "refresh_token_expire_days": os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"),
}

# Google OAuth 설정
OAUTH_GOOGLE_CONFIG = {
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
    "scope": "openid email profile"
}


