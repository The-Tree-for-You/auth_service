# Build stage
FROM python:3.12 as builder
WORKDIR /app

## Install poetry and dependencies
RUN pip install --upgrade pip && pip install poetry
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev


# Runtime stage
FROM python:3.12-alpine
WORKDIR /auth_service

## Build stage에서 설치한 의존성 복사
COPY --from=builder /app /app
COPY . /app

EXPOSE 8000

## uvicorn을 사용하여 비동기 방식으로 FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
