# Posts (Auth CRUD + Reactions/Report) API v1 — MVP(Project Level 1)
StageLog 백엔드에서 Posts 도메인의 **로그인 필요 기능**(게시글/댓글 CRUD, 좋아요/싫어요, 신고)까지 포함하는 앱입니다.
(+기존 Public(조회) API와의 통합)

---

## 1) 요약 (추가/확장된 기능)
---

- **게시글 작성/수정/삭제** (로그인 필요)
- **댓글 작성/수정/삭제** (로그인 필요)
- **좋아요/싫어요(토글/스위치)** (로그인 필요 + 트랜잭션/중복 방지)
- **신고** (로그인 필요 + 중복 방지)

### 기존 Public 기능
- 공연별 게시글 목록: `GET /api/events/<event_id>/posts`
- 게시글 상세: `GET /api/posts/<post_id>`
- 댓글 목록(페이지네이션): `GET /api/posts/<post_id>/comments`

---

## 2) 한 줄 실행(로컬, Docker Compose)

> 프로젝트 루트(stagelog-backend repo root)에서 실행

```bash
docker compose -p stagelog up -d --build
```

### 상태 확인
```bash
docker compose -p stagelog ps
docker compose -p stagelog logs -f api (혹은 --tail=100 등)
```
" Windows 사용으로 인한 포트 이슈가 있는 경우,
`.env`에 `API_PORT=18000` 설정후 `http://localhost:18000`으로 확인 <ISSUE#2 참조>

---

## 3) 로컬 개발 흐름
### 컨테이너 구성
- `stagelog-api`: Django API 서버
- `stagelog-db`: MariaDB 11.8.3
### 마이그레이션
- 모델 변경 시 아래 순서 필수
1. 모델 수정
2. 마이그레이션 생성
3. 마이그레이션 적용
4. 적용 여부 확인
### 명령어 (docker 환경 기준)
```bash
1) 마이그레이션 파일 생성
docker compose -p stagelog exec api python manage.py makemigrations posts

1-1) (선택) migrate 전 SQL 확인(검증용, 실제 적용되지 않음)
docker compose -p stagelog exec api python manage.py sqlmigrate posts <migration_number>

2) DB에 적용
docker compose -p stagelog exec api python manage.y migrate

3) 적용 확인
docker compose -p stagelog exec api python manage.py showmigrations posts
```

---

## 4) API 엔드포인트 요약
" 공통: 응답은 `common_resonse()` 형태를 따릅니다.
" 로그인 필요 API는 **`Authorization: Baerer <access_token>`** 헤더가 필요합니다.

### 4-1. Public (토큰 불필요)
- GET /api/events/<event_id>/posts : 공연별 게시글 목록(페이지네이션/검색/정렬)
- GET /api/posts/<post_id> : 게시글 상세(조회수 증가 포함)
- GET /api/posts/<post_id>/comments : 댓글 목록(페이지네이션)

### 4-2. Auth Required
**게시글 CRUD**
- POST /api/events/<event_id>/posts : 게시글 작성
- PATCH /api/posts/<post_id> : 게시글 수정(작성자만)
- DELETE /api/posts/<post_id> : 게시글 삭제(작성자만)

**댓글 CRUD**
- POST /api/posts/<post_id>/comments : 댓글 작성
- PATCH /api/comments/<comment_id> : 댓글 수정(작성자만)
- DELETE /api/comments/<comment_id> : 댓글 삭제(작성자만)

**좋아요/싫어요**
- POST /api/posts/<post_id>/reactions/like : 좋아요 토글/스위치
- POST /api/posts/<post_id>/reactions/dislike : 싫어요 토글/스위치

**신고**
- POST /api/posts/<post_id>/reports : 신고 접수(중복 신고 방지)

---

### 5) 데이터 모델 요약 (posts/models.py)
**주요 테이블**
- `posts`: 게시글
- `comments`: 댓글
- `post_reactions`: 좋아요/싫어요 (유저당 게시글 1개 반응만)
- `reports`: 신고(유저당 게시글 1회만 신고 가능)

**정합성/중복 방지**
- `PostReaction`: `UniqueConstraint(user, post)
- `Report`: `UniqueContraint(user, post)
- 좋아요/싫어요 처리: `transaction.atomic + select_for_update + F()`로 동시적으로 카운트 정합성 유지

---

## 6) Front 통합 가이드
1. event 목록 API 에서 받은 `event_id`(INT PK)로만 호출 (`kopis_id`는 내부 저장/매핑용)
2. 로그인 API는 모두 헤더 필요: `Authorization: Bearer <access_token>
3. 댓글은 게시글 상세와 분리된 API 제공(페이지네이션)
4. 페이지네이션 파라미터(`page`, `size)와 응답 메터(`total_count`, `total_pages`)를 사용
5. trailing slash 없이 호출

## 7) DB/ETL 통합 가이드
1. ETL 적재 시 `events.event_id`의 안정적인 생성/유지 중요
2. `repots.report_detail` 현재 NULLABLE 처리

## 8) 파일/라우팅 참고
- `apps/posts/models.py`: Post/Comment/Reaction/Report 모델
- `apps/posts/views.py`: Posts API 로직(공개+로그인 기능)
- `apps/posts/urls.py`: `/api/posts/...` 라우팅
- `apps/posts/comment_urls.py` : `/api/comments/...` 라우팅 분리
- `config/urls.py` : 앱 include 단일 소스

## 9) 그 외
- `category`, `reason_ctegory` 등 문자열 필드 허용 값 리스트 결정(정보, 질문, 후기, 잡담 등)
