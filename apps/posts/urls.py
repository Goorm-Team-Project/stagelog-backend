from django.urls import path
from . import views

urlpatterns = [
    path("<int:post_id>/comments", views.post_comments_list, name="post_comments_list"),
    path("<int:post_id>", views.post_detail, name="post_detail"),
]