# apps/bookmarks/views.py

from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from apps.common.utils import common_response, login_check
from events.models import Event
from bookmarks.models import Bookmark
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

@csrf_exempt
@require_http_methods(["POST"]) # POST만 허용
@login_check # 토큰 검증 필수
def toggle_bookmark(request, event_id):
    try:
        user_id = request.user_id
        
        # 1. 유저 & 공연 객체 조회
        try:
            user = User.objects.get(user_id=user_id)
            event = Event.objects.get(event_id=event_id)
        except (User.DoesNotExist, Event.DoesNotExist):
            return common_response(False, message="잘못된 요청입니다(유저 또는 공연 없음).", status=404)

        # 2. 토글 로직 (있으면 삭제, 없으면 생성)
        bookmark = Bookmark.objects.filter(user=user, event=event).first()

        if bookmark:
            bookmark.delete()
            return common_response(True, message="북마크 취소됨", data={"state": "off"}, status=200)
        else:
            Bookmark.objects.create(user=user, event=event)
            return common_response(True, message="북마크 성공!", data={"state": "on"}, status=201)

    except Exception as e:
        print(f"Bookmark Error: {e}")
        return common_response(False, message="서버 에러 발생", status=500)