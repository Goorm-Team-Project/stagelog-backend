from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.views.decorators.http import require_GET

from common.utils import common_response
from .models import Post

# Create your views here.
def _post_summary(p: Post) -> dict:
    return {
        "post_id": p.post_id,
        "event_id": p.event_id,
        "user_id": p.user_id,
        "nickname": getattr(p.user, "nickname", None),
        "category": p.category,
        "title": p.title,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
        "views": p.views,
        "like": p.like_count,
        "dislike": p.dislike_count,
    }

def _post_detail(p: Post) -> dict:
    return {
        **_post_summary(p),
        "content": p.content,
    }

@require_GET
def event_posts_list(request, event_id: int):
    category = (request.GET.get("category") or "").strip()
    search = (request.GET.get("search") or "").strip()
    sort  = (request.GET.get("sort") or "latest").strip().lower()

    try:
        page = int(request.GET.get("page") or 1)
        size = int(request.GET.get("size") or 10) #(optinal: size)
    except ValueError:
        return common_response(False, message="page/size는 정수여야 합니다.", status=400)

    qs = Post.objects.filter(event_id=event_id).select_related("user")

    if category:
        qs = qs.filter(category=category)

    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

    # 정렬: 최신/인기(좋아요)/조회수
    if sort in ("popular", "like", "likes"):
        qs = qs.order_by("-like_count", "-created_at", "-post_id")
    elif sort in ("views", "view"):
        qs = qs.order_by("-views", "-created-at)", "-post_id")
    else:
        qs = qs.order_by("-created_at", "-post_id")
    
    paginator = Paginator(qs, size)
    page_obj = paginator.get_page(page)

    data = {
        "event_id": str(event_id),
        "posts": [_post_summary(p) for p in page_obj.object_list],
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "page": page_obj.number,
        "size": size,
    }
    return common_response(True, data=data, message="공연별 게시글 목록 조회 성공", status=200)


@require_GET
def post_detail(request, post_id: int):
    # 조회수 +1 (동시성 안전)
    updated = Post.objects.filter(post_id=post_id).update(views=F("views") + 1)
    if updated == 0:
        return common_response(False, message="존재하지 않는 게시글입니다.", status=404)
    
    p = Post.objects.select_related("user").get(post_id=post_id)
    return common_response(True, data=_post_detail(p), message="게시글 상세 조회 성공", status=200)