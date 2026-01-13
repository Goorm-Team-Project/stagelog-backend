from django.urls import path
from . import views
from posts import views as post_views

urlpatterns = [
    # 목록은 config에서 /api/events로 직접 매핑 path('', views.event_list, name='event_list'),
    path('<int:event_id>', views.event_detail, name='event_detail'),
    path('<int:event_id>/posts', post_views.event_posts_list, name='event_posts_list'),
]