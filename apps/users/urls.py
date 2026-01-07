from django.urls import path
from .views import kakao_login, me, signup, kakao_test_page, kakao_callback_test, get_user_info, get_other_user_info, update_user_profile

urlpatterns = [
    #카카오 로그인
    path('login/kakao', kakao_login, name='kakao_login'),
    # path('login/google', google_login, name='google_login'),
    # path('login/naver', naver_login, name='naver_login'),
    #회원가입
    path('signup', signup, name='signup'),
    #마이페이지
    path('me', get_user_info, name='get_user_info'),
    #다른 유저 정보 조회
    path('<int:user_id>', get_other_user_info, name='get_other_user_info'),
    #내 정보 수정
    path('me/profile', update_user_profile, name='update_user_profile'),

    #테스트용
    path('kakao/test', kakao_test_page),      # 1. 여기로 접속하면 로그인 시작
    path('callback', kakao_callback_test),
]