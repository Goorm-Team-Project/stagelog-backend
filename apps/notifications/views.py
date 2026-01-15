from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Notification
from common.utils import common_response, login_check
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_safe, require_http_methods 

def _notification_summary(n: Notification) -> dict:
    return {
        "notification_id": n.notification_id,
        "type": n.type,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
        "post_id": n.post_id if n.post_id else None,
        "event_id": n.event_id if n.event_id else None
    }

@require_safe
@csrf_exempt
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

    except Exception as e:
        print(f"에러 로그: {e}") 
        return common_response(success=False, message="서버 에러", status=500)

@require_safe
@csrf_exempt
@login_check
def get_unread_notification(request):
    try:
        user_id = request.user_id

        unread_count = Notification.objects.filter(
            user_id=user_id,
            is_read=False
        ).count()

        return common_response(success=True, message="체크 완료", data={
                "has_unread": unread_count > 0,
                "unread_count": unread_count
            },
            status=200
        )
    except Exception as e:
        return common_response(success=False, message="서버 에러", status=500)

@require_http_methods(["PATCH"])
@csrf_exempt
@login_check
def read_notification(request, notification_id):
    try:
        notification = Notification.objects.get(
            notification_id=notification_id, 
            user_id=request.user_id 
        )
        
        if not notification.is_read:
            notification.is_read = True
            notification.save()

        return common_response(success=True, message="읽음 처리 완료", status=200)

    except Notification.DoesNotExist:
        return common_response(success=False, message="존재하지 않는 알림입니다.", status=404)
    except Exception as e:
        return common_response(success=False, message="서버 에러", status=500)