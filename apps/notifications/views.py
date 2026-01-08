from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Notification
from common.utils import common_response, login_check

@login_check
def get_notification_list(request):
    try:
        user_id = request.user_id

        notifications = Notification.objects.filter(user_id=user_id).order_by('-created_at')

        type_param = request.GET.get('type')
        if type_param and type_param in Notification.Type.values:
            notifications = notifications.filter(type=type_param)


            