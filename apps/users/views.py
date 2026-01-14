import traceback, json, sys, requests
import os, datetime, jwt, uuid
from .models import User, RefreshToken
from django.conf import settings
from django.views.decorators.http import require_POST, require_safe, require_http_methods 
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from apps.common.utils import (
    create_access_token, 
    create_refresh_token,
    create_register_token,
    common_response, 
    login_check
)

# redirect, HttpResponse 임포트 확인
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse

User = get_user_model()

@require_safe 
def kakao_test_page(request):
    client_id = settings.KAKAO_REST_API_KEY
    redirect_uri = settings.KAKAO_REDIRECT_URI
    url = f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(url)

@require_safe
def kakao_callback_test(request):
    code = request.GET.get('code')
    return HttpResponse(f"""
        <h1>인가 코드 발급 완료!</h1>
        <p>아래 코드를 복사해서 curl 요청에 쓰세요:</p>
        <textarea cols="100" rows="5">{code}</textarea>
    """)

@require_safe
def naver_test_page(request):
    client_id = settings.NAVER_REST_API_KEY
    
    redirect_uri = settings.NAVER_REDIRECT_URI
    
    state = str(uuid.uuid4())
    
    url = f"https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&state={state}"
    
    return redirect(url)

@require_safe
def google_test_page(request):
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    client_id = settings.GOOGLE_REST_API_KEY
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    scope = "https://www.googleapis.com/auth/userinfo.profile"
    state = str(uuid.uuid4())
    
    url = f"{base_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state={state}"
    
    return redirect(url)

@require_safe
def google_callback_test(request):
    """
    2. 구글에서 코드를 받아와서 -> 바로 토큰 교환 -> 유저 정보 출력 (원스톱)
    """
    code = request.GET.get('code')
    
    if not code:
        return JsonResponse({"error": "코드가 없습니다."}, status=400)

    # A. 토큰 발급 요청
    token_req_url = "https://oauth2.googleapis.com/token"
    req_data = {
        "code": code,
        "client_id": settings.GOOGLE_REST_API_KEY,
        "client_secret": settings.GOOGLE_ACCESS_TOKEN_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    token_res = requests.post(token_req_url, data=req_data)
    token_json = token_res.json()
    
    if 'access_token' not in token_json:
        return JsonResponse({"error": "토큰 발급 실패", "details": token_json}, status=400)
        
    google_access_token = token_json.get('access_token')

    # B. 유저 정보 요청
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {google_access_token}"}
    
    user_res = requests.get(user_info_url, headers=headers)
    user_info = user_res.json()

    # C. 결과 출력
    return JsonResponse({
        "message": "구글 로그인 테스트 성공!",
        "token": token_json,
        "user_info": user_info
    }, json_dumps_params={'ensure_ascii': False})

@require_safe
def naver_callback_test(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code:
        return JsonResponse({"error": "코드가 없습니다."}, status=400)

    # 1. 네이버한테 "토큰 내놔" 요청 (Access Token 발급)
    token_url = "https://nid.naver.com/oauth2.0/token"
    token_params = {
        "grant_type": "authorization_code",
        "client_id" : settings.NAVER_REST_API_KEY,
        "redirect_uri" : settings.NAVER_REDIRECT_URI,
        "code" : code,
        "client_secret" : settings.NAVER_ACCESS_TOKEN_CLIENT_SECRET,
        "state": state
    }
    
    token_res = requests.get(token_url, params=token_params)
    token_json = token_res.json()
    
    if 'access_token' not in token_json:
        return JsonResponse(token_json, status=400)
        
    access_token = token_json.get('access_token')

    # 2. 토큰으로 "유저 정보 내놔" 요청 (User Info)
    user_info_url = "https://openapi.naver.com/v1/nid/me"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    user_res = requests.get(user_info_url, headers=headers)
    user_info = user_res.json()

    # 3. 브라우저 화면에 결과 바로 뿌리기 (성공!)
    return JsonResponse({
        "message": "로그인 테스트 성공!",
        "token_data": token_json,
        "user_info": user_info
    }, json_dumps_params={'ensure_ascii': False})

@csrf_exempt
@require_POST # POST만 허용
def kakao_login(request):
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식입니다.", status=400)
        
        code = data.get('code')
        if not code:
            return common_response(success=False, message="인가 코드 에러.", status=400)
        
        access_token_req_url = "https://kauth.kakao.com/oauth/token"
        access_token_req_data = {
            "grant_type": "authorization_code",
            "client_id" : settings.KAKAO_REST_API_KEY,
            "redirect_uri" : settings.KAKAO_REDIRECT_URI,
            "code" : code,
            "client_secret" : settings.KAKAO_ACCESS_TOKEN_CLIENT_SECRET
        }

        token_res = requests.post(access_token_req_url, data=access_token_req_data)

        if token_res.status_code != 200:
            print(f"Kakao token error: {token_res.json()}", flush=True) 
            return common_response(success=False, message="카카오 액세스 토큰 발급 실패", status=400)
        
        kakao_access_token = token_res.json().get('access_token')

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {kakao_access_token}"}
        users_res = requests.get(user_info_url, headers=headers)

        if users_res.status_code != 200:
            print(f"Kakao User Info Error: {users_res.json()}", flush=True)
            return common_response(success=False, message="사용자 정보 조회 실패", status=500)

        user_info = users_res.json()
        provider_id = str(user_info.get('id'))
        
        return social_login('kakao', provider_id, None)
    
    except Exception as e:
        traceback.print_exc()
        return common_response(success=False, message="서버 에러", status=500)

@csrf_exempt
@require_POST
def naver_login(request):
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식입니다.", status=400)
        
        code = data.get('code')
        state = data.get('state')
        if not code or not state:
            return common_response(success=False, message="인가 코드 에러.", status=400)
        
        access_token_req_url = "https://nid.naver.com/oauth2.0/token"
        access_token_req_data = {
            "grant_type": "authorization_code",
            "client_id" : settings.NAVER_REST_API_KEY,
            "redirect_uri" : settings.NAVER_REDIRECT_URI,
            "code" : code,
            "client_secret" : settings.NAVER_ACCESS_TOKEN_CLIENT_SECRET,
            "state": state
        }

        token_res = requests.post(access_token_req_url, data=access_token_req_data)

        if token_res.status_code != 200:
            print(f"Kakao token error: {token_res.json()}", flush=True) 
            return common_response(success=False, message="네이버 액세스 토큰 발급 실패", status=400)
        
        naver_access_token = token_res.json().get('access_token')

        user_info_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {naver_access_token}"}
        users_res = requests.get(user_info_url, headers=headers)

        if users_res.status_code != 200:
            print(f"Naver User Info Error: {users_res.json()}", flush=True)
            return common_response(success=False, message="네이버 사용자 정보 조회 실패", status=500)

        user_info = users_res.json().get('response')
        provider_id = str(user_info.get('id'))
        
        return social_login('naver', provider_id, None)
    
    except Exception as e:
        traceback.print_exc()
        return common_response(success=False, message="서버 에러", status=500)


@csrf_exempt
@require_POST
def google_login(request):
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식입니다.", status=400)
        
        code = data.get('code')
        
        if not code:
            return common_response(success=False, message="인가 코드 에러.", status=400)

        # 1. 구글 토큰 발급 요청
        access_token_req_url = "https://oauth2.googleapis.com/token"
        access_token_req_data = {
            "grant_type": "authorization_code",
            "client_id": settings.GOOGLE_REST_API_KEY,
            "client_secret": settings.GOOGLE_ACCESS_TOKEN_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "code": code
        }

        token_res = requests.post(access_token_req_url, data=access_token_req_data)

        if token_res.status_code != 200:
            print(f"Google token error: {token_res.json()}", flush=True)
            return common_response(success=False, message="구글 액세스 토큰 발급 실패", status=400)
        
        google_access_token = token_res.json().get('access_token')

        # 2. 구글 사용자 정보 조회
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {google_access_token}"}
        
        users_res = requests.get(user_info_url, headers=headers)

        if users_res.status_code != 200:
            print(f"Google User Info Error: {users_res.json()}", flush=True)
            return common_response(success=False, message="사용자 정보 조회 실패", status=500)

        user_info = users_res.json()
        
        provider_id = str(user_info.get('id'))
        
        return social_login('google', provider_id, None)
    
    except Exception as e:
        traceback.print_exc()
        return common_response(success=False, message="서버 에러", status=500)
        
        
def social_login(provider, provider_id, email=None):
    try:        
        user = User.objects.filter(provider='provider', provider_id=provider_id).first()
        
        if user:
            jwt_access_token = create_access_token(user.user_id)
            refresh_token = create_refresh_token(user.user_id)

            RefreshToken.objects.create(user=user, token=refresh_token)
            return common_response(
                success=True,
                message=f"{user.nickname} 님! 환영합니다!",
                data={
                    "access_token": jwt_access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": user.user_id,
                        "nickname": user.nickname,
                        "level": user.level
                    }
                },
                status=200)
        
        else:
            email = None # 카카오 비즈앱 아니면 이메일 못 가져올 수 있음
            try:
                register_token = create_register_token("kakao", provider_id, email)
            except Exception as e:
                traceback.print_exc() # [수정] file=sys.stdout 제거 (버퍼링 방지)
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
        traceback.print_exc()
        return common_response(success=False, message="알 수 없는 오류", status=500)


@csrf_exempt
@require_POST # 회원가입도 POST
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
        
        # ... (중략: 토큰 검증 및 회원가입 로직) ...
        try:
            payload = jwt.decode(register_token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return common_response(success=False, message="만료된 토큰입니다.", status=401)
        except jwt.InvalidTokenError:
            return common_response(success=False, message="유효하지 않은 토큰입니다.", status=401)

        provider = payload.get('provider')
        provider_id = payload.get('provider_id')

        if not provider or not provider_id:
             return common_response(success=False, message="토큰에 필수 정보(provider)가 없습니다.", status=400)

        if User.objects.filter(email=input_email).exists():
            return common_response(success=False, message="이미 가입된 이메일입니다.", status=409)

        user = User.objects.create_user(
            email=input_email,
            nickname=input_nickname,
            provider=provider,
            provider_id=provider_id,
            is_email_sub=is_email_sub,
            is_events_notification_sub=is_events_notification_sub,
            is_posts_notification_sub=is_posts_notification_sub,
        )

        access_token = create_access_token(user.user_id)
        
        return common_response(
            success=True,
            message="가입 완료", 
            data={"access_token": access_token},
            status=201
        )

    except Exception as e:
        traceback.print_exc()
        return common_response(success=False, message="서버 내부 오류", status=500)

@require_safe
@login_check
def me(request):
    try:
        user = User.objects.get(user_id=request.user_id)

        return common_response(
            success=True,
            message="유저 정보 조회 성공",
            data={
                "user": {
                    "id": user.user_id,
                    "nickname": user.nickname,
                    "level": user.level
                }
            },
            status=200
        )

    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", status=404)
    except Exception as e:
        return common_response(success=False, message="서버 에러 발생", status=500) # static -> status 수정


@require_safe
@login_check
def get_user_info(request):
    try:
        user_id = request.user_id
        user = User.objects.get(user_id=user_id)
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
            },
            status=200
        )
    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", status=404)
    except Exception as e:
        print(f"에러 발생 : {e}")
        traceback.print_exc()
        return common_response(success=False, message="정보 조회 중 서버 오류 발생", status=500)

@require_safe # GET 조회
@login_check # 여기 require_safe랑 login_check 순서 주의 (api_view 없으니 login_check가 안쪽, 즉 아래)
def get_other_user_info(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)
        public_data = {
            "id": user.user_id,
            "nickname": user.nickname,
            "level": user.level,
            "exp": user.exp,
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
@require_http_methods(["PATCH"])
@login_check
def update_user_profile(request):
    try:
        user_id = request.user_id
        user = User.objects.get(user_id=user_id)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식입니다.", status=404)
        
        # ... (중략: 수정 로직) ...
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
                # ... (데이터 반환) ...
                "nickname": user.nickname,
                # ...
                "bookmarks": bookmarked_id
            },
            status=200
        )
    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", status=404)
    except Exception as e:
        return common_response(success=False, message="서버 에러", status=500)

@csrf_exempt
@require_POST
def refresh_token_check(request):
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return common_response(success=False, message="잘못된 JSON 형식", status=400)

        client_refresh_token = data.get('refresh_token')
        

        if not client_refresh_token:
            return common_response(success=False, message="토큰이 없습니다.", status=400)

        try:
            payload = jwt.decode(client_refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return common_response(success=False, message="만료된 토큰입니다.", status=401)
        except jwt.InvalidTokenError as e:
            return common_response(success=False, message="유효하지 않은 토큰입니다.", status=401)

        is_exist = RefreshToken.objects.filter(user_id=user_id, token=client_refresh_token).exists()
        if not is_exist:
            return common_response(success=False, message="유효하지 않거나 만료된 토큰입니다.", status=401)

        user = User.objects.get(user_id=user_id)
        new_access_token = create_access_token(user.user_id)

        return common_response(
            success=True,
            message="토큰 재발급 완료",
            data={"access_token": new_access_token},
            status=200
        )
    except User.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 회원입니다.", stats=404)
    except Exception as e:
        print(f"[DEBUG] FATAL ERROR: {e}", flush=True)
        traceback.print_exc()
        return common_response(success=False, message="유효하지 않은 토큰입니다.", status=401)


@csrf_exempt
@require_POST
@login_check
def logout(request):
    try:
        data = json.loads(request.body)
        delete_target_token = data.get('refresh_token')

        if not delete_target_token:
            return common_response(success=False, message="삭제할 토큰이 없습니다.", status=400)
        
        RefreshToken.objects.filter(
            user_id=request.user_id,
            token=delete_target_token
        ).delete()

        return common_response(success=True, message="로그아웃 성공", status=200)

    except Exception as e:
        return common_response(success=True, message="로그아웃 처리됨")