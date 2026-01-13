# apps/bookmarks/urls.py

from django.urls import path
from .views import toggle_bookmark, mypage

urlpatterns = [
    # 엔드포인트: /api/bookmarks/1 (POST)
    path('/<int:event_id>', toggle_bookmark, name='toggle_bookmark'),
    # 마이페이지
    path('/mypage', mypage, name='mypage'),
]