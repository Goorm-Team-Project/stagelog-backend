from django.urls import path
from .views import kakao_login, me

urlpatterns = [
    path('login/kakao', kakao_login, name='kakao_login'),
    path('login/google', google_login, name='google_login'),
    path('login/naver', naver_login, name='naver_login'),
    path('signup', signup, name='signup'),
    path('me', me, name='user_me'),
]