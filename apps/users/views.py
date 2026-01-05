import traceback
import json
import requests
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
    POST /users/login/kakao/
    Body: { "access_token": "카카오_액세스_토큰" }
    기능: 카카오 토큰 유효성 검증 -> 유저 DB 조회/생성 -> JWT 발급
    """
    if request.method != 'POST':
        return common_response(success=False, message="POST 요청만 가능합니다.", status=405)

    try:
        # 1. 프론트엔드(Client)에서 보낸 카카오 토큰 받기
        data = json.loads(request.body)
        kakao_token = data.get('access_token')

        if not kakao_token:
            return common_response(success=False, message="카카오 액세스 토큰이 필요합니다.", status=400)


        # 2. [Real] 카카오 서버에 "이 토큰 진짜니?" 물어보기
        headers = {"Authorization": f"Bearer {kakao_token}"}
        kakao_response = requests.get("https://kapi.kakao.com/v2/user/me", headers=headers)

        # 3. 토큰이 유효하지 않으면 카카오가 에러 뱉음
        if kakao_response.status_code != 200:
            return common_response(success=False, message="유효하지 않은 카카오 토큰입니다.", status=401)

        # 4. 카카오 프로필 정보 추출
        user_info = kakao_response.json()
        # kakao_account = user_info.get('kakao_account', {})
        # profile = kakao_account.get('profile', {})

        # 이메일은 필수 (카카오 개발자 센터에서 이메일 제공 동의 필수 설정 필요)
        input_email = data.get('email')
        input_nickname = data.get('nickname')
        provider_id = str(user_info.get('id')) # 카카오 고유 ID
        # nickname = profile.get('nickname', f'User{provider_id[:4]}')

        if not input_email:
            return common_response(success=False, message="이메일 정보가 없습니다.", status=400)
        if not input_nickname:
            return common_response(success=False, message="닉네임 정보가 없습니다.", status=400)

        # 5. [DB 처리] 회원가입 or 로그인
        try:
            # 5-1. 이미 가입된 유저 찾기
            user = User.objects.get(email=input_email)
            message = "로그인 성공"
            
            # (선택) 닉네임이 바뀌었으면 업데이트
            # if user.nickname != nickname:
            #     user.nickname = nickname
            #     user.save()

        except User.DoesNotExist:
            # 5-2. 없으면 새로 생성 (회원가입)
            # models.py에 정의된 UserManager의 create_user 사용
            user = User.objects.create_user(
                email=input_email,
                nickname=input_nickname,
                provider='kakao',
                provider_id=provider_id
            )
            message = "회원가입 및 로그인 성공"

        # 6. [JWT 발급] 우리 서비스 전용 토큰 생성 (utils.py 사용)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return common_response(
            success=True, 
            message=message, 
            data={
                "token": {
                    "access": access_token, 
                    "refresh": refresh_token
                },
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "level": user.level # models.py 기본값 확인
                }
            },
            status=200
        )

    except Exception as e:
        # 실제 운영 시에는 로깅 필요
        # print(f"Login Error: {e}")
        print("======================== 에러 로그 =======================", flush=True)
        traceback.print_exc()
        print("======================== 에러 로그 =======================", flush=True)

        return common_response(success=False, message="서버 내부 오류 발생", status=500)

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