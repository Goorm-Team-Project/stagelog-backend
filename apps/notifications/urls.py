from django.urls import path
from .views import get_notification_list, get_unread_notification

urlpatterns = [
    path("", get_notification_list, name='get_notification_list'),
    path("/check", get_unread_notification, name='get_unread_notification')
]