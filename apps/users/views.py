import traceback, json, sys, requests
import os, datetime, jwt
from .models import User
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from apps.common.utils import (
    create_access_token, 
    create_refresh_token,
    create_register_token,
    common_response, 
    login_check
)

User = get_user_model()

# apps/users/views.py
from django.shortcuts import redirect
from django.http import HttpResponse

# [테스트 1] 카카오 로그인 페이지로 납치하는 함수
def kakao_test_page(request):
    client_id = settings.KAKAO_REST_API_KEY
    redirect_uri = settings.KAKAO_REDIRECT_URI
    
    # 카카오 로그인 URL 생성
    url = f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    
    return redirect(url)

# [테스트 2] 카카오가 코드를 던져줄 'Callback' 처리 함수
def kakao_callback_test(request):
    code = request.GET.get('code')
    
    # 화면에 코드를 큼지막하게 보여줌 (복사하기 편하게)
    return HttpResponse(f"""
        <h1>인가 코드 발급 완료!</h1>
        <p>아래 코드를 복사해서 curl 요청에 쓰세요:</p>
        <textarea cols="100" rows="5">{code}</textarea>
    """)

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
        KAKAO_ACCESS_TOKEN_CLIENT_SECRET = settings.KAKAO_ACCESS_TOKEN_CLIENT_SECRET
        KAKAO_REST_API_KEY = settings.KAKAO_REST_API_KEY
        KAKAO_REDIRECT_URI = settings.KAKAO_REDIRECT_URI
        
        access_token_req_data = {
            "grant_type": "authorization_code",
            "client_id" : KAKAO_REST_API_KEY,
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

        user_info = users_res.json()
        provider_id = str(user_info.get('id'))

        """
        provider_id 이용해서 DB에 유저 정보 확인하기
        """
        
        user = User.objects.filter(provider='kakao', provider_id=provider_id).first()
        
        """
        존재하는 유저 로그인 성공
        """
        if user:
            jwt_access_token = create_access_token(user.id)
            return common_response(
                success=True,
                message=f"{user.nickname} 님! 환영합니다!",
                data={
                    "access_token": jwt_access_token
                }
                status=200)
        
        else:
            try:
                register_token = create_register_token("kakao", provider_id, email)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                return common_response(success=False, message="등록 토큰 인코딩 실패", status=500)
            return common_response(
                success=True,
                message="회원가입이 필요합니다.",
                data={
                    "register_token": register_token,
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
        
        # 1. 토큰 검사
        if not register_token:
            return common_response(success=False, message="토큰이 없습니다.", status=400)

        try:
            # [중요] algorithms는 리스트여야 함
            payload = jwt.decode(register_token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return common_response(success=False, message="만료된 토큰입니다.", status=401)
        except jwt.InvalidTokenError:
            return common_response(success=False, message="유효하지 않은 토큰입니다.", status=401)

        # 2. 토큰에서 핵심 정보 추출 (★ 여기가 핵심)
        # 프론트가 뭘 보내든 상관없이, 토큰에 적힌 provider를 믿습니다.
        provider = payload.get('provider')
        provider_id = payload.get('provider_id')

        if not provider or not provider_id:
             return common_response(success=False, message="토큰에 필수 정보(provider)가 없습니다.", status=400)

        # 3. 중복 가입 방지 (이메일 기준)
        if User.objects.filter(email=input_email).exists():
            return common_response(success=False, message="이미 가입된 이메일입니다.", status=409)

        # 4. 유저 생성 (동적으로 들어온 provider 사용)
        user = User.objects.create_user(
            email=input_email,
            nickname=input_nickname,
            provider=provider,
            provider_id=provider_id
        )

        # 5. 로그인 토큰 발급
        access_token = create_access_token(user.id)
        
        return common_response(success=True, message="가입 완료", data={"access_token": access_token})

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return common_response(success=False, message="서버 내부 오류", status=500)


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