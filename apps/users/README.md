# Users App

Django 기반 사용자 인증 및 프로필 관리 앱

## 개요

카카오 OAuth 로그인, JWT 기반 인증, 사용자 프로필 관리 기능을 제공하는 Django 앱입니다.

## 주요 기능

- 카카오 OAuth 2.0 소셜 로그인
- JWT 기반 Access Token / Refresh Token 인증
- 사용자 회원가입 및 프로필 관리
- 레벨, 경험치, 신뢰도 점수 시스템
- 북마크 기능 연동
- 알림 구독 설정 (이메일, 이벤트, 게시글)

## 모델 구조

### User 모델
```python
- user_id: 기본키 (AutoField)
- email: 이메일 (고유값)
- nickname: 닉네임
- provider: OAuth 제공자 (kakao, google, naver 등)
- provider_id: OAuth 제공자의 사용자 ID
- created_at: 가입일시
- is_email_sub: 이메일 구독 여부
- is_events_notification_sub: 이벤트 알림 구독 여부
- is_posts_notification_sub: 게시글 알림 구독 여부
- is_admin: 관리자 권한
- exp: 경험치
- level: 레벨
- reliability_score: 신뢰도 점수 (기본값: 50)
- is_active: 활성 상태
```

### RefreshToken 모델
```python
- user: User 외래키
- token: Refresh Token 문자열
- created_at: 생성일시
```

## 환경 변수 설정

`.env` 파일에 다음 항목을 추가해야 합니다:

```env
KAKAO_REST_API_KEY=your_kakao_rest_api_key
KAKAO_REDIRECT_URI=your_redirect_uri
KAKAO_ACCESS_TOKEN_CLIENT_SECRET=your_client_secret
SECRET_KEY=your_django_secret_key
```

## API 엔드포인트

### 인증

#### 카카오 로그인
```
POST /api/users/login/kakao
Content-Type: application/json

{
  "code": "kakao_authorization_code"
}
```

**응답 (기존 회원)**
```json
{
  "success": true,
  "message": "{nickname} 님! 환영합니다!",
  "data": {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token"
  }
}
```

**응답 (신규 회원 - 회원가입 필요)**
```json
{
  "success": true,
  "message": "회원가입이 필요합니다.",
  "data": {
    "register_token": "jwt_register_token"
  }
}
```

#### 회원가입
```
POST /api/users/signup
Content-Type: application/json

{
  "register_token": "jwt_register_token",
  "nickname": "사용자닉네임",
  "email": "user@example.com",
  "is_email_sub": false,
  "is_events_notification_sub": false,
  "is_posts_notification_sub": false
}
```

**응답**
```json
{
  "success": true,
  "message": "가입 완료",
  "data": {
    "access_token": "jwt_access_token"
  }
}
```

#### Access Token 재발급
```
POST /api/users/login/refresh
Content-Type: application/json

{
  "refresh_token": "jwt_refresh_token"
}
```

**응답**
```json
{
  "success": true,
  "message": "토큰 재발급 완료",
  "data": {
    "access_token": "new_jwt_access_token"
  }
}
```

#### 로그아웃
```
POST /api/users/logout
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "refresh_token": "jwt_refresh_token"
}
```

**응답**
```json
{
  "success": true,
  "message": "로그아웃 성공"
}
```

### 사용자 정보

#### 내 정보 조회
```
GET /api/users/me
Authorization: Bearer {access_token}
```

**응답**
```json
{
  "success": true,
  "message": "정보 조회 성공",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "nickname": "사용자닉네임",
    "provider": "kakao",
    "provider_id": "123456789",
    "created_at": "2026-01-09T12:00:00Z",
    "is_email_sub": false,
    "is_events_notification_sub": false,
    "is_posts_notification_sub": false,
    "is_admin": false,
    "exp": 100,
    "level": 2,
    "reliability_score": 55,
    "bookmarks": [1, 2, 3]
  }
}
```

#### 다른 사용자 정보 조회
```
GET /api/users/{user_id}
Authorization: Bearer {access_token}
```

**응답**
```json
{
  "success": true,
  "message": "정보 조회 성공",
  "data": {
    "id": 2,
    "nickname": "다른사용자",
    "level": 5,
    "exp": 500
  }
}
```

#### 내 프로필 수정
```
PATCH /api/users/me/profile
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "nickname": "새로운닉네임",
  "is_email_sub": true,
  "is_events_notification_sub": true,
  "is_posts_notification_sub": false
}
```

**응답**
```json
{
  "success": true,
  "message": "정보 수정 성공",
  "data": {
    "id": 1,
    "nickname": "새로운닉네임",
    "bookmarks": [1, 2, 3]
  }
}
```

## 테스트 가이드 (curl)

### 1. 개발 환경 실행
```bash
docker compose up
```

### 2. 카카오 인가 코드 발급
브라우저에서 다음 URL로 접속:
```
http://localhost:8000/api/users/kakao/test
```

카카오 로그인 후 표시되는 인가 코드를 복사합니다.

### 3. 로그인 (토큰 발급)
```bash
curl -X POST http://localhost:8000/api/users/login/kakao \
-H "Content-Type: application/json" \
-d '{
    "code": "YOUR_AUTH_CODE"
}'
```

### 4. 내 정보 조회
```bash
curl -X GET http://localhost:8000/api/users/me \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 인증 방식

- **Access Token**: API 요청 시 `Authorization: Bearer {token}` 헤더로 전송
- **Refresh Token**: Access Token 만료 시 재발급 요청에 사용
- **Register Token**: 신규 회원가입 시 임시 인증 토큰

## 주요 유틸리티 함수

- `create_access_token(user_id)`: Access Token 생성
- `create_refresh_token(user_id)`: Refresh Token 생성
- `create_register_token(provider, provider_id, email)`: Register Token 생성
- `login_check`: 데코레이터 - JWT 인증 검증
- `common_response(success, message, data, status)`: 통일된 API 응답 형식

## 보안 고려사항

### CSRF 보호
Django는 기본적으로 POST, PUT, PATCH, DELETE 요청에 CSRF 토큰 검증을 수행합니다. 하지만 REST API에서는 다음 이유로 `@csrf_exempt`를 사용합니다:

- **JWT 기반 인증**: 쿠키 대신 Authorization 헤더로 JWT를 전송하므로 CSRF 공격 위험이 낮음
- **외부 클라이언트**: 모바일 앱, 프론트엔드 SPA 등 다양한 클라이언트가 접근
- **OAuth 콜백**: 카카오 서버에서 리다이렉트되는 요청은 CSRF 토큰을 포함할 수 없음

**적용 위치**: POST/PATCH 요청을 받는 모든 API 엔드포인트
```python
@csrf_exempt
@require_POST
def kakao_login(request):
    ...
```

### 기타 보안
- JWT 토큰: SECRET_KEY 기반 서명
- Refresh Token: 데이터베이스에 저장하여 관리
- 비밀번호: OAuth 전용이므로 `set_unusable_password()` 사용

## 에러 응답 예시

```json
{
  "success": false,
  "message": "에러 메시지",
  "status": 400
}
```

## 참고 자료

- [카카오 로그인 REST API 문서](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api)
- Django Authentication System
- JWT (JSON Web Token)