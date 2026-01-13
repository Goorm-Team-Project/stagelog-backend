from django.urls import path
from . import views
from posts import views as post_views

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path('/<int:event_id>', views.event_detail, name="event_detail"),
    path('/<int:event_id>/posts', post_views.event_posts_list, name="event_posts_list"),
]