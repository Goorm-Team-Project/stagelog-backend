from django.urls import path
from .views import kakao_login, me, signup, kakao_test_page, kakao_callback_test

urlpatterns = [
    path('login/kakao', kakao_login, name='kakao_login'),
    # path('login/google', google_login, name='google_login'),
    # path('login/naver', naver_login, name='naver_login'),
    path('signup', signup, name='signup'),
    path('me', me, name='user_me'),

    path('kakao/test', kakao_test_page),      # 1. 여기로 접속하면 로그인 시작
    path('callback', kakao_callback_test),
]