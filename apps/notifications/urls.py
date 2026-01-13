from django.urls import path
from .views import get_notification_list, get_unread_notification, read_notification

urlpatterns = [
    # path('', get_notification_list, name='get_notification_list'),
    ## 목록은 config에서 /api/notifications로 직접 매핑
    path('check', get_unread_notification, name='get_unread_notification'),
    path('<int:notification_id>/read', read_notification, name='read_notification')
]