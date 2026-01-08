from django.urls import path
from .views import get_notification_list

urlpatterns = [
    path("", get_notification_list, name='get_notification_list'),
]