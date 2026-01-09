import traceback, json, sys, requests
import os, datetime, jwt
from .models import User
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_safe
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
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식입니다.", status=400)
        
        code = data.get('code') #카카오에서 발급한 인가 코드
        if not code:
            return common_response(success=False, message="인가 코드 에러.", status=400)

        access_token_req_url = "https://kauth.kakao.com/oauth/token" #POST 요청 사용
        
        access_token_req_data = {
            "grant_type": "authorization_code",
            "client_id" : settings.KAKAO_REST_API_KEY,
            "redirect_uri" : settings.KAKAO_REDIRECT_URI,
            "code" : code,
            "client_secret" : settings.KAKAO_ACCESS_TOKEN_CLIENT_SECRET
        }

        token_res = requests.post(access_token_req_url, data=access_token_req_data)

        if token_res.status_code != 200:
            print(f"Kakao token error: {toekn.res.json()}", flush=True)
            return common_response(success=False, message="카카오 액세스 토큰 발급 실패", status=400)
        
        """
        액세스 토큰 발급 이후 사용자 정보 조회
        """

        kakao_access_token = token_res.json().get('access_token')

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {kakao_access_token}"}
        users_res = requests.get(user_info_url, headers=headers)

        if users_res.status_code != 200:
            print(f"Kakao User Info Error: {users_res.json()}", flush=True)
            return common_response(success=False, message="사용자 정보 조회 실패", status=500)

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
            jwt_access_token = create_access_token(user.user_id)
            refresh_token = create_refresh_token(user.user_id)

            RefreshToken.objects.create(user=user, token=refresh_token)
            return common_response(
                success=True,
                message=f"{user.nickname} 님! 환영합니다!",
                data={
                    "access_token": jwt_access_token,
                    "refresh_token": refresh_token
                },
                status=200)
        
        else:
            email=None
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
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식입니다.", status=400)


        register_token = data.get('register_token')
        input_nickname = data.get('nickname')
        input_email = data.get('email')
        is_email_sub = data.get('is_email_sub', False)
        is_events_notification_sub = data.get('is_events_notification_sub', False)
        is_posts_notification_sub = data.get('is_posts_notification_sub', False)

        if not register_token or not input_nickname or not input_email:
            return common_response(success=False, message="필수 정보가 없습니다.", status=400)
        
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
            provider_id=provider_id,
            is_email_sub=is_email_sub,
            is_events_notification_sub=is_events_notification_sub,
            is_posts_notification_sub=is_posts_notification_sub,
            
        )

        # 5. 로그인 토큰 발급
        access_token = create_access_token(user.user_id)
        
        return common_response(
            success=True,
            message="가입 완료", 
            data={"access_token": access_token},
            status=201
        )

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
                "id": user.user_id, 
                "email": user.email, 
                "nickname": user.nickname,
                "role": "admin" if user.is_admin else "user"
            }
        )
    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", status=404)

#/api/user/me 내 정보 조회
@login_check
def get_user_info(request):
    try:
        user_id = request.user_id #데코레이터에서 받아옴
        
        user = User.objects.get(user_id=user_id) # db에서 해당하는 user id 의 정보 가져오기

        bookmarked_id = list(user.bookmarks.values_list('event_id', flat=True))

        return common_response(
            success=True,
            message="정보 조회 성공",
            data={
                "id": user.user_id,
                "email": user.email,
                "nickname": user.nickname,
                "provider": user.provider,
                "provider_id": user.provider_id,
                "created_at": user.created_at,
                "is_email_sub": user.is_email_sub,
                "is_events_notification_sub": user.is_events_notification_sub,
                "is_posts_notification_sub": user.is_posts_notification_sub,
                "is_admin": user.is_admin,
                "exp": user.exp,
                "level": user.level,
                "reliability_score": user.reliability_score,
                "bookmarks": bookmarked_id
                #뱃지는 테이블 생성 후에
            },
            status=200
        )
    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", status=404)
    except Exception as e:
        print(f"에러 발생 : {e}")
        traceback.print_exc()
        return common_response(success=False, message="정보 조회 중 서버 오류 발생", status=500)


@require_safe
@login_check
def get_other_user_info(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)

        public_data = {
            "id": user.user_id,
            "nickname": user.nickname,
            "level": user.level,
            #"reliability_score": user.reliability_score,
            "exp": user.exp,
            # 뱃지는 테이블 생성 후에
        }
        
        return common_response(
            success=True,
            message="정보 조회 성공",
            data=public_data,
            status=200
        )

    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 유저입니다.", status=404)
    except Exception as e:
        return common_response(success=False, message="서버 에러", status=500)

@csrf_exempt
@login_check
def update_user_profile(request):
    try:
        user_id = request.user_id
        user = User.objects.get(user_id=user_id)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식입니다.", status=404)
        
        if 'nickname' in body:
            new_nickname = body['nickname']
            if user.nickname != new_nickname:
                if User.objects.filter(nickname=new_nickname).exists():
                    return common_response(success=False, message="이미 존재하는 닉네임입니다.", status=409)
                user.nickname = new_nickname

        if 'is_email_sub' in body:
            user.is_email_sub = body['is_email_sub']

        if 'is_events_notification_sub' in body:
            user.is_events_notification_sub = body['is_events_notification_sub']

        if 'is_posts_notification_sub' in body:
            user.is_posts_notification_sub = body['is_posts_notification_sub']

        user.save()

        bookmarked_id = list(user.bookmarks.values_list('event_id', flat=True))

        return common_response(
            success=True,
            message="정보 수정 성공",
            data={
                "id": user.user_id,
                "email": user.email,
                "nickname": user.nickname,
                "provider": user.provider,
                "provider_id": user.provider_id,
                "created_at": user.created_at,
                "is_email_sub": user.is_email_sub,
                "is_events_notification_sub": user.is_events_notification_sub,
                "is_posts_notification_sub": user.is_posts_notification_sub,
                "is_admin": user.is_admin,
                "exp": user.exp,
                "level": user.level,
                "reliability_score": user.reliability_score,
                "bookmarks": bookmarked_id
                #뱃지는 테이블 생성 후에
            },
            status=200
        )
    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", status=404)
    except Exception as e:
        return common_response(success=False, message="서버 에러", status=500)

def refresh_token_check(request):
    try:
        data = json.loads(request.body)
        client_refresh_token = data.get('refresh_token')

        if not client_refresh_token:
            return common_response(success=False, message="토큰이 없습니다.", status=400)

        # 1차 검증
        payload = jwt.decode(client_refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')

        # 2차 검증
        if not RefreshToken.objects.filter(user_id=user_id, token=client_refresh_token).exists():
            return common_response(success=False, message="만료된 토큰입니다. 다시 로그인 하세요", status=401)

        # 검증 통과
        user = User.objects.get(id=user_id)

        new_access_token = create_access_token(user.user_id)

        return common_response(
            success=True,
            message="토큰 재발급 완료",
            data={"access_token": new_access_token},
            status=200
        )
    except jwt.ExpiredSignatureError:
        return common_response(success=False, message="리프레시 토큰이 만료됐습니다. 다시 로그인하세요", status=401)
    except (jwt.DecodeError, User.DoesNotExist):
        return common_response(success=False, message="유효하지 않은 토큰입니다.", status=401)
    except Exception as e:
        return common_response(success=False, message="서버 에러", status=500)

def logout(request):
    try:
        data = json.loads(request.body)
        delete_target_token = data.get('refresh_token')

        if not delete_target_token:
            return common_response(success=False, message="삭제할 토큰이 없습니다.", status=400)

        RefreshToken.objects.filter(
            user=request.user,
            token=delete_target_token
        ).delete()

        return common_response(success=True, message="로그아웃 성공", status=200)

    except Exception as e:
        return common_response(success=True, message="로그아웃 처리됨")