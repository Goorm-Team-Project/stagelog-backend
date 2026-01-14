# apps/bookmarks/views.py

from django.views.decorators.http import require_http_methods, require_safe
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage

from common.utils import common_response, login_check
from events.models import Event
from .models import Bookmark

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


@require_safe 
@login_check
def mypage(request):
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('size', 1))

        bookmarks = Bookmark.objects.filter(user_id=request.user_id).select_related('event').order_by('-created_at')

        paginator = Paginator(bookmarks, page_size)

        try:
            current_page_data = paginator.page(page)
        except EmptyPage:
            current_page_data = []

        event_list = []
        for bookmark in current_page_data:
            event = bookmark.event
            event_list.append({
                "event_id": event.event_id, 
                "title": event.title,
                "artist": event.artist if hasattr(event, 'artist') else "",
                "start_date": event.start_date.strftime('%Y-%m-%d') if event.start_date else None,
                "end_date": event.end_date.strftime('%Y-%m-%d') if event.end_date else None,
                "venue": event.venue,
                "poster": event.poster.url if event.poster else None
            })

        return common_response(
            success=True,
            message="즐겨찾기 목록 조회 성공",
            data={
                "events": event_list,
                "has_next": current_page_data.has_next(),
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
            },
            status=200
        )
        
    except Exception as e:
        print(f"[ERROR] mypage: {e}") # 디버깅용 로그 추가
        return common_response(success=False, message="서버 에러", status=500)
    