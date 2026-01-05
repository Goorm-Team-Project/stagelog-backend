from django.urls import path
from . import views

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path('<int:event_id>', views.event_detail, name="event_detail"),
    #추후 users/auth/posts/comments도 동일한 방식으로 여기에 붙이기
]