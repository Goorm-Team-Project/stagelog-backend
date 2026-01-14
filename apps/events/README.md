# Events (공연) API v1 - MVP(Project Level 1)

StageLog 백엔드의 **공연 목록 조회/공연 상세 조회** 기능을 담당하는 앱입니다.
현재 백엔드는 **Pure Django(함수 기반 뷰)**로 구현하는 것으로 백앤드 내부 합의됐으며,
공통 응답 포맷은 `common_response()`를 사용합니다.
(success : 성공 여부(boolean), message: FE(Client)에 보내줄 메시지(string), data: 실제 payload(object|array|null)

---

## 1) 요약 (events 브랜치/기능)
- 구현 범위(MVP 1차)
    - `GET /api/events` : 전체 공연 목록 조회(검색/정렬/페이지네이션)
    - `GET /api/events/<event_id>` : 특정 공연 상세 조회

- ID 정책(팀 합의/ERD latest 기준)
    - `event_id` : **내부 PK (INT)**
    - `kopis_id` : **KOPIS 공연 ID (VARCHAR)**

---

## 2) 한 줄 실행 (Docker Compose)
> ** `docker-compose.yml` 이 있는 프로젝트 루트에서 실행하세요.
```bash
cd /mnt/c/(로컬 루트 디렉터리...)/(프로젝트 루트)
docker compose up -d --build
docker dompose ps
```
정상이라면 `stagelog-api`, `stagelog-db`가 UP 상태로 떠야합니다.

---

## 3) 로컬 접속 확인(라우팅)
- Django 기본 화면(루트)
    - `http://localhost:8000/`
- Events API:
    - 목록: `http//localhost:8000/api/events`
    - 상세: `http//localhost:8000/api/events/1`

---

## 4) 마이그레이션 명령
- models.py 변경사항을 DB에 반영하기 위한 파일 생성 (makemigrations)
- 실제 DB에 적용 (migrate)
### 실행 명령
```bash
# 1 마이그레이션 파일 생성 (evnets 앱만)
docker compose exec api python manage.py makemigrations events
# 2 DB에 적용
docker compose exec api python manage.py migrate
# 3 적용 여부 확인
docker compose exec api python manage.py showmigrations events
```

---

## 5) (현재 v1) API 구현 범위
### 5-1) GET /api/events (공연 목록 조회)
**Query params**
- `search` : 검색어
- `sort` : 정렬 기준 (`name`, `latest` 등)
- `page` : 페이지 번호
- `size` : 페이지당 개수
**Response 예시**
```json
{
    "success": true,
    "message": "",
    "data": {
        "events": [
            {
                "event_id": 1,
                "kopis_id": "PF278277",
                .
                .
                .
            }
        ],
        "total_count": 150,
        "total_pages": 20
    }
}
```

---

### 5-2) GET /api/events/<event_id> (공연 상세 조회)
**Path Param**
- `event_id` (INT): 내부 PK
**Response 예시(성공)**
```json
{
    "success": true,
    "message": "",
    "data": {
        "event_id": 1,
        "kopis_id": "PF278277",
        .
        .
        .
    }
}
```
**Response 예시(실패)**
```json
{
  "success": false,
  "message": "존재하지 않는 공연 ID",
  "data": null
}
```

---

### 6) FE/DB(ETL) 통합 포인트
**Frontend(React)**
- 호출 엔드포인트 기준: `http://localhost:8000`
- 요청 URL을 명세서와 100% 동일하게 고정
- 목록에 필요한 최소 필드:
    - event_id, title, artist, start_date, end_date, venue, poster
**DB/ETL**
- 이벤트 데이터 적재 시,:
    - 내부 PK `event_id`는 DB에서 INT로 관리
    - 외부 KOPIS 공연 ID는 `kopis_id로 VARCHAR 저장
- Date Format: 날짜 구분자 (.)이 아닌, (-)하이픈 포맷 변환 필요.
- 초기 더미데이터/적재 없으면 목록/상세는 "데이터 없음(빈 배열/404)"이 정상.
-> 이 모델에 null=True 설정되어 있으므로 일부 표시데이터 없다면 ""이 아닌 NULL 처리 필요.

---

### 7) DB 접속
db 컨테이너에서 바로 접속
`docker compose exec db mariadb -u test -p stagelog

### 8) 그 외 사항
즐겨찾기 기준 정렬 관련:
- 로그인/북마크 기능 붙이는 시점에 적용
- '개인 기준(사용자 식별+북마크 조인 필오)', '전체 인기 기준(북마크 집계 필요)' 정의에 따라 구현 예정

