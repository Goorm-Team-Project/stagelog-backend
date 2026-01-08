from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Notification
from common.utils import common_response, login_check

def _notification_summary(n: Notification) -> dict:
    return {
        "notification_id": n.notification_id,
        "type": n.type,
        "maessage": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
        "post_id": n.post_id if n.post_id else None,
        "event_id": n.event_id if n.event_id else None
    }

@login_check
def get_notification_list(request):
    try:
        user_id = request.user_id

        # 1. 입력값 검증
        try:
            page = int(request.GET.get("page") or 1)
            size = 20
        except ValueError:
            return common_response(success=False, message="page는 정수여야 합니다.", status=400)

        qs = Notification.objects.filter(user_id=user_id).order_by('-created_at')

        type_param = (request.GET.get('type') or "").strip()
        if type_param and type_param in Notification.Type.values:
            qs = qs.filter(type=type_param)

        paginator = Paginator(qs, size)
        page_obj = paginator.get_page(page)

        data = {
            "notifications": [_notification_summary(n) for n in page_obj.object_list],
            "has_next": page_obj.has_next(),
            "total_count": paginator.count,
        }

        return common_response(success=True, data=data, message="알림 조회 성공", status=200)
        # ---------------------------------------------------------

    except Exception as e:
        print(f"에러 로그: {e}") # 디버깅용 로그 찍어주면 좋습니다
        return common_response(success=False, message="서버 에러", status=500)