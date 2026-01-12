# 로컬 실행 (팀 표준: Docker)
```
cp .env.example .env
docker compose up -d --build
# (옵션) 로그 확인
docker compose logs -f api
```

# 컨테이너 재시작/내리기
```
docker compose down
docker compose up -d --build
```
