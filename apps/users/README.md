# User apps
로그인/마이페이지 관련 Apps

### 참고 페이지
https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#before-you-begin-process


### .env 에 반드시 포함되어야 하는 목록
KAKAO_REST_API_KEY 카카오 개발자 페이지에서 등록된 앱의 REST API KEY
KAKAO_REDIRECT_URI 카카오 개발자 페이지에서 등록된 앱에 등록한 리다이렉트 URI
KAKAO_ACCESS_TOKEN_CLIENT_SECRET 동일 앱에 설정된 클라이언트 시크릿


## 🧪 API 테스트 가이드 (Curl)

프론트엔드 없이 터미널에서 **카카오 로그인 -> 토큰 발급 -> 내 정보(북마크 포함) 조회**를 테스트하는 방법입니다.

### 1. 카카오 로그인 (인가 코드로 토큰 발급)
세팅된 docker compose로 api 서버와 db 서버를 docker compose up
컨테이너 api 서버로 접속 가능하게 세팅

### STEP 1
브라우저에서 컨테이너주소/api/auth/kakao/test 로 접속.
카카오 로그인 페이지에서 이메일/비밀번호 입력

이후 발급된 인가코드를 아래 YOUR_AUTH_CODE 에 붙여넣기 한 후 요청

**요청 (POST)**
curl -X POST http://localhost:8000/api/users/login/kakao \
-H "Content-Type: application/json" \
-d '{
    "code": "YOUR_AUTH_CODE"
}'

백엔드 내부에서 카카오 서버에 해당 유저에 대한 고유 id 등 프로필에 대한 데이터 요청.

응답으로 발급된 토큰을 아래 <발급받은_ACCESS_TOKEN> 에 붙여넣기 하면 내 정보 조회


curl -X GET http://localhost:8000/api/users/me \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <발급받은_ACCESS_TOKEN>"