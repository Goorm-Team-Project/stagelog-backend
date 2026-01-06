from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_GET

from common.utils import common_response
from .models import Event
from django.shortcuts import render

# Create your views here.
# Point: 검색/정렬/페이지네이션 최소 단위 기능 구현.

def _event_summary(e: Event) -> dict:
    return {
        "event_id": e.event_id,
        "kopis_id": e.kopis_id,
        "title": e.title,
        "artist": e.artist,
        "start_date": e.start_date.isoformat(),
        "end_date": e.end_date.isoformat(),
        "venue": e.venue,
        "poster": e.poster,
    }

def _event_detail(e: Event) -> dict:
    return {
        "event_id": e.event_id,
        "kopis_id": e.kopis_id,
        "title": e.title,
        "artist": e.artist,
        "start_date": e.start_date.isoformat(),
        "end_date": e.end_date.isoformat(),
        "venue": e.venue,
        "area": e.area,
        "age": e.age,
        "poster": e.poster,
        "time": e.time,
        "price": e.price,
        "relate_url": e.relate_url,
        "host": e.host,
        "genre": e.genre,
        "update_date": e.update_date.isoformat() if e.update_date else None,   
    }


@require_GET
def event_list(request):
    search = (request.GET.get("search") or "").strip()
    sort = (request.GET.get("sort") or "name").strip().lower()

    #page/size 기본값
    try:
        page = int(request.GET.get("page") or 1)
        size = int(request.GET.get("size") or 10)
    except ValueError:
        return common_response(False, message="page/size는 정수여야 합니다.", status=400)
    
    if page <= 0 or size <= 0 or size > 100:
        return common_response(False, message="page는 1 이상, size는 1~100 범위에 포함되어야 합니다.", status=400)
    
    qs = Event.objects.all()

    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(artist__icontains=search) |
            Q(venue__icontains=search)
        )

    #--정렬 매핑 (팀 노션 명세의 sort 값이 확정되면 이 부분 수정)--
    if sort in ("latest", "recent"):
        qs = qs.order_by("-start_date", "-event_id")
    elif sort in ("update",):
        qs = qs.order_by("-update_date", "-event_id")
    else:
        # default: 이름순
        qs = qs.order_by("title", "event_id")

    paginator = Paginator(qs, size)
    page_obj = paginator.get_page(page)

    data = {
        "events": [_event_summary(e) for e in page_obj.object_list],
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "page": page_obj.number,
        "size": size,
    }
    return common_response(True, data=data, message="성공적으로 목록을 불러옴", status=200)


@require_GET
def event_detail(request, event_id: int):
    try:
        e = Event.objects.get(event_id=event_id)
    except Event.DoesNotExist:
        return common_response(False, message="존재하지 않는 공연 ID", status=404)

    return common_response(True, data=_event_detail(e), message="성공적으로 데이터 반환", status=200)
