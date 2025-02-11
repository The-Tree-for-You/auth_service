from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from ..core.config import DB_CONFIG

# Define the database URL
## 환경변수 TEST_ENV가 1일 경우 테스트 DB를 사용하도록 설정

# Create the SQLAlchemy engine
if 'sqlite' in DB_CONFIG['postgresql']['sqlalchemy_url']:
    engine = create_engine(DB_CONFIG['postgresql']['sqlalchemy_url'], connect_args={"check_same_thread": False})
else:
    engine = create_engine(DB_CONFIG['postgresql']['sqlalchemy_url'])

# Create the SQLAlchemy session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 모델의 베이스 클래스
Base = declarative_base()

# DB 세션을 반환하는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()