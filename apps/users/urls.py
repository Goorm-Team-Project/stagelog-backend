from django.urls import path
from .views import kakao_login, me

urlpatterns = [
    path('login', kakao_login, name='kakao_login'),
    path('me', me, name='user_me'),
]