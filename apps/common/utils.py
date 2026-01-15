import jwt
import datetime
import functools
import math

from django.http import JsonResponse, HttpResponse
from django.conf import settings

def health_check(request):
    return HttpResponse("OK", status=200)

def user_exp_calculator(base_exp, user_level, decay_factor=0.1):
    """
    base_exp : 활동으로 획득하는 점수(글쓰기, 댓글 ...)
    user_level : 현재 유저의 레벨
    decay_factor : 경험치 획득 감소 계수
    """
    if user_level < 1:
        user_level = 1
    
    multiplier = 1 / (1 + (decay_factor * (user_level - 1)))
    exp = base_exp * multiplier

    return max(1, round(exp))

def common_response(success=True, data=None, message="", status=200):
    """
    API 공통 응답 함수
    :param success: 성공 여부 (True/False)
    :param data: 반환할 데이터 (Dictionary or List)
    :param message: 클라이언트에게 보낼 메시지
    :param status: HTTP 상태 코드
    """
    payload = {
        "success": success,
        "message": message,
        "data": data,
    }
    # status 코드는 HTTP 응답 헤더에 설정됨
    return JsonResponse(payload, status=status, json_dumps_params={'ensure_ascii': False})

# 2. 액세스 토큰 생성 함수
def create_access_token(user_id):
    """
    User ID를 받아 JWT 액세스 토큰을 생성
    """
    payload = {
        'user_id': user_id,
        # settings에 설정한 시간(예: 30분) 후 만료
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS),
        'iat': datetime.datetime.utcnow(), # 발급 시간
    }
    
    # PyJWT encode
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def create_refresh_token(user_id):
    """
    Refresh Token 생성 (유효기간: 예시 2주)
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(weeks=2), # 2주
        'iat': datetime.datetime.utcnow(),
        'type': 'refresh' # 토큰 타입 명시
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

# 회원가입용 임시 토큰 생성 함수
def create_register_token(provider, provider_id, email):
    payload = {
        "provider": provider,
        "provider_id": provider_id,
        "email": email,
        # 가입용은 짧게 (예: 10분)
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

# 3. 토큰 검증 함수 (데코레이터로 쓸 수도 있고 직접 호출도 가능)
def validate_token(token):
    """
    토큰을 받아 유효성을 검증하고, 유효하면 payload(user_id 포함)를 반환
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # 토큰 만료
    except jwt.InvalidTokenError:
        return None  # 위변조되거나 잘못된 토큰

def login_check(func):
    """
    API 뷰에 사용할 데코레이터
    """
    def wrapper(request, *args, **kwargs):
        # 헤더에서 Authorization 가져오기
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return common_response(success=False, message="토큰이 없거나 형식이 잘못되었습니다.", status=401)
        
        # 'Bearer' 떼기
        token = auth_header.split(' ')[1]

        # 토큰 검증
        payload = validate_token(token)

        if payload is None:
            return common_response(success=False, message="유효하지 않거나 만료된 토큰입니다.", status=401)

        # 검증 통과. request에 user_id넣기
        request.user_id = payload['user_id']

        return func(request, *args, **kwargs)
    
    return wrapper

# Optional Auth 헬퍼 추가
def get_optional_user_id(request):
    """
    Authorization 헤더가 없으면 (None, None) 반환 -> Public 유지
    Authorization 헤더가 있으면 토큰 검증:
      - 유효: (user_id, None)
      - 무효/형식오류: (None, error_msg)  -> 호출부에서 401 처리
    """
    auth = request.headers.get("Authorization")
    if not auth:
        return None, None

    if not auth.startswith("Bearer "):
        return None, "토큰 형식이 잘못되었습니다. (Bearer 토큰)"

    token = auth.split(" ", 1)[1].strip()
    decoded = validate_token(token)
    if decoded is None:
        return None, "유효하지 않거나 만료된 토큰입니다."

    user_id = decoded.get("user_id")
    if not user_id:
        return None, "토큰에 user_id가 없습니다."

    return user_id, None