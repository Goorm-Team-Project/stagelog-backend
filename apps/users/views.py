import traceback, json, sys, requests
from .models import User
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from apps.common.utils import (
    create_access_token, 
    create_refresh_token, 
    common_response, 
    login_check
)

User = get_user_model()

@csrf_exempt
def kakao_login(request):
    """
    REST API KEY + 클라이언트 시크릿으로 카카오 auth 서버에 인가코드 요청. >> 프론트엔드 영역
    인가코드 발급 후 액세스 토큰 요청. >> 여기서부터 백엔드 영역
    발급된 액세스 토큰으로 사용자 정보 조회 등 실시.
    https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api 참고
    """
    try:
        data = json.loads(request.body)
        code = data.get('code') #카카오에서 발급 인가 코드
        if not code:
            return common_response(success=False, message="인가 코드 에러.", status=400)

        access_token_req_url = "https://kauth.kakao.com/oauth/token" #POST 요청 사용
        #KAKAO_ACCESS_TOKEN_CLIENT_SECRET = .env에서 클라이언트 시크릿 가져오기
        KAKAO_REST_API_KEY = #.env 에서 앱에 할당된 REST API 가져오기
        KAKAO_REDIRECT_URI = #.env 에서 앱에 등록한 응답 리다이렉트 주소
        
        access_token_req_data = {
            "grant_type": "authorization_code",
            "cliend_id" : KAKAO_REST_API_KEY,
            "redirect_uri" : KAKAO_REDIRECT_URI,
            "code" : code,
            "client_secret" : KAKAO_ACCESS_TOKEN_CLIENT_SECRET
        }

        token_res = requests.post(access_token_req_url, data=access_token_req_data)

        if token_res.status_code != 200:
            return common_response(success=False, message="카카오 액세스 토큰 발급 실패", status=400)
        
        """
        액세스 토큰 발급 이후 사용자 정보 조회
        """

        kakao_access_token = token_res.json().get('access_token')

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {kakao_access_token}"}
        users_res = requests.get(user_info_url, headers=headers)

        if users_res.status_code != 200:
            return common_response(success=False, message="사용자 정보 조회 실패", status=400)

        user_info = user_res.json()
        provider_id = str(user_info.get('id'))

        """
        provider_id 이용해서 DB에 유저 정보 확인하기
        """
        
        user = User.objects.filter(provider='kakao', provider_id=provider_id).first()

        if user:
            jwt_access_token = create_access_token(user.id)
            return common_response(success=True, message="f{user.nickname} 님! 환영합니다!", status=200)
        
        else:
            register_payload = {
                "provider" : "kakao",
                "provider_id" : provider_id,
                "email" : user_info.get('kakao_account', {}).get('email', ''),
                "exp" : datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
            }
            register_token = jwt.encode(register_payload, SECRET_KEY, algorithm="HS256")
            return common_response(
                success=True,
                message="회원가입이 필요합니다.",
                data={
                    "register_token": register_token,
                    "email" : register_payload["email"]
                },
                status=202
            )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return common_response(success=False, message="알 수 없는 오류", status=500)

@csrf_exempt
def signup(request):
    try:
        data = json.loads(request.body)
        register_token = data.get('register_token')
        input_nickname = data.get('nickname')
        input_email = data.get('email')
        input_provider = data.get('provider')

        if not register_token:
            return common_response(success=False, message="회원가입 JWT 토큰이 없습니다.", status=400)

        try:
            payload = jwt.decode(register_token, SECRET_KEY, algorithm="HS56"])
        except jwt.ExpiredSignatureError:
            return common_response(success=False, message="가입 시간이 만료되었습니다.", status=400)
        except jwt.InvalidTokenError:
            return common_response(succes=False, message="유효하지 않은 토큰입니다.", status=400)

        provider_id = payload.get('provider_id')

        if User.objects.filter(provider='kakao', provider_id=provider_id).exists():
            return common_response(succes=False, message="이미 가입된 회원입니다.", status=400)
        if User.objects.filter(email=email).exists():
            return common_response(succes=False, message="이미 가입된 회원입니다.", status=400)
        
        user = User.objects.create_user(
            email=input_email,
            nickname=input_nickname,
            provider=input_provider,
            provider_id=provider_id
        )

        access_token = create_access_token(user.id)
        return common_response(success=Ture, message"회원가입이 완료되었습니다.", data={"acess_token": access_token})

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return common_response(succes=False, message="에러 발생", status=500)


# 내 정보 조회 (토큰 검증 테스트용)
@login_check
def me(request):
    try:
        # login_check 데코레이터가 request.user_id를 세팅해줌
        user = User.objects.get(id=request.user_id)
        return common_response(
            success=True, 
            message="조회 성공",
            data={
                "id": user.id, 
                "email": user.email, 
                "nickname": user.nickname,
                "role": "admin" if user.is_admin else "user"
            }
        )
    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", status=404)