from django.urls import path
from . import views

# 게시글 상세, 댓글 목록 API 분리

urlpatterns = [
    #커뮤니티 (전체 게시글 목록)은 config에서 /api/posts로 직접 매핑 path('', views.posts_list, name='post_list'),

    # 댓글 목록
    path('<int:post_id>/comments', views.post_comments_list, name='post_comments_list'),

    # 게시글 상세
    path('<int:post_id>', views.post_detail, name='post_detail'),

    # 좋아요/싫어요
    path('<int:post_id>/reactions/like', views.post_like, name='post_like'),
    path('<int:post_id>/reactions/dislike', views.post_dislike, name='post_dislike'),
    
    # 신고
    path('<int:post_id>/reports', views.post_report, name='post_report'),
]