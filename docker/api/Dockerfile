FROM python:3.12.3-slim

WORKDIR /app

# mysqlclient 빌드에 필요한 의존성(목적: WSL/로컬 차이 제거)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# 운영환경을 위해 소스 코드 전체를 이미지 안에 넣기
COPY . /app/

# 소스는 volume mount로 개발(빠른 빌드). 운영에서는 COPY 방식으로 변경
EXPOSE 8000

