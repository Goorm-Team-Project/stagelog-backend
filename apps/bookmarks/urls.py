# apps/bookmarks/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 엔드포인트: /api/bookmarks/1 (POST)
    path("<int:event_id>", views.toggle_bookmark, name="toggle_bookmark"),
    # 마이페이지
    path("mypage", views.mypage, name="mypage"),
]