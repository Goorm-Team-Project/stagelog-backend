FROM python:3.12.3-slim

WORKDIR /app

# 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. requirements.txt 복사 (Context가 루트이므로 파일명만 적어도 됨)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# 2. [추가] 운영 환경을 위해 소스 코드 전체를 이미지 안에 넣기
COPY . /app/

EXPOSE 8000

# 3. [추가] 실행 명령 (ETL과 달리 백엔드는 서버가 계속 떠있어야 함)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]

