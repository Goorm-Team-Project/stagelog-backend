import json

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError

from common.utils import common_response, login_check
from events.models import Event
from .models import Post, Comment, PostReaction, Report, ReactionType

# Create your views here.

# 고정 카테고리: 후기/질문/정보
CATEGORY_MAP = {
    "review": "후기", "후기": "후기",
    "question": "질문", "질문": "질문",
    "info": "정보", "정보": "정보",
}

def normalize_category(raw: str):
    if raw is None:
        return None
    v = raw.strip()
    if not v:
        return None
    key = v.lower()
    return CATEGORY_MAP.get(key) or CATEGORY_MAP.get(v)


def _parse_json(request):
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None
def _post_summary(p: Post) -> dict:
    return {
        "post_id": p.post_id,
        "event_id": p.event_id,
        "user_id": p.user_id,
        "nickname": getattr(p.user, "nickname", None),
        "category": p.category,
        "title": p.title,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "views": p.views,
        "like": p.like_count,
        "dislike": p.dislike_count,
    }

def _post_detail(p: Post) -> dict:
    return {
        **_post_summary(p),
        "content": p.content,
    }

def _comment_item(c: Comment) -> dict:
    return {
        "comment_id": c.comment_id,
        "post_id": c.post_id,
        "user_id": c.user_id,
        "nickname": getattr(c.user, "nickname", None),
        "content": c.content,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }

# 커뮤니티 > 전체 게시글 목록
@csrf_exempt
@require_GET
def posts_list(request):
    category = normalize_category(request.GET.get("category"))  # 전체면 None
    search = (request.GET.get("search") or "").strip()
    sort  = (request.GET.get("sort") or "latest").strip().lower()

    try:
        page = int(request.GET.get("page") or 1)
        size = int(request.GET.get("size") or 10)
    except ValueError:
        return common_response(False, message="page/size는 정수여야 합니다.", status=400)

    if page <= 0 or size <= 0 or size > 100:
        return common_response(False, message="page는 1 이상, size는 1~100 범위에 포함되어야 합니다.", status=400)

    qs = Post.objects.select_related("user", "event")

    if category:
        if category not in ("후기", "질문", "정보"):
            return common_response(False, message="category는 전체/후기/질문/정보 중 하나여야 합니다.", status=400)
        qs = qs.filter(category=category)

    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

    if sort in ("popular", "like", "likes"):
        qs = qs.order_by("-like_count", "-created_at", "-post_id")
    elif sort in ("views", "view"):
        qs = qs.order_by("-views", "-created_at", "-post_id")
    else:
        qs = qs.order_by("-created_at", "-post_id")

    paginator = Paginator(qs, size)
    page_obj = paginator.get_page(page)

    posts = []
    for p in page_obj.object_list:
        posts.append({
            **_post_summary(p),
            # ✅ 커뮤니티 리스트에 “어느 공연 글인지” 필요
            "event": {
                "event_id": p.event_id,
                "title": getattr(p.event, "title", None),
                "poster": getattr(p.event, "poster", None),
            }
        })

    data = {
        "posts": posts,
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "page": page_obj.number,
        "size": size,
    }
    return common_response(True, data=data, message="전체 게시글 목록 조회 성공", status=200)



# 공연별 > 게시글 목록
@csrf_exempt
@require_http_methods(["GET", "POST"])
def event_posts_list(request, event_id: int):

    if request.method == "POST":
        return event_posts_create(request, event_id)
    category = normalize_category(request.GET.get("category"))
    search = (request.GET.get("search") or "").strip()
    sort  = (request.GET.get("sort") or "latest").strip().lower()

    try:
        page = int(request.GET.get("page") or 1)
        size = int(request.GET.get("size") or 10) #(optinal: size)
    except ValueError:
        return common_response(False, message="page/size는 정수여야 합니다.", status=400)

    qs = Post.objects.filter(event_id=event_id).select_related("user")

    # '전체'는 category 파라미터 안보내는 방식으로 처리
    if category:
        if category not in ("후기", "질문", "정보"):
            return common_response(False, message="category는 전체/후기/질문/정보 중 하나여야 합니다.", status=400)
        qs = qs.filter(category=category)

    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

    # 정렬: 최신/인기(좋아요)/조회수
    if sort in ("popular", "like", "likes"):
        qs = qs.order_by("-like_count", "-created_at", "-post_id")
    elif sort in ("views", "view"):
        qs = qs.order_by("-views", "-created_at", "-post_id")
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

@csrf_exempt
@login_check
@require_POST
def event_posts_create(request, event_id: int):
    # 공연 존재 확인
    if not Event.objects.filter(event_id=event_id).exists():
        return common_response(False,message="존재하지 않는 공연입니다.", status=404)

    data= _parse_json(request)
    if data is None:
        return common_response(False, message="잘못된 JSON 형식입니다.", status=400)
    
    category = normalize_category(data.get("category"))
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    image_url = (data.get("image_url") or "").strip() or None

    if not category or not title or not content:
        return common_response(False, message="카테고리/제목/내용는 필수입니다.", status=400)

    if category not in ("후기", "질문", "정보"):
        return common_response(False, message="category는 후기/질문/정보 중 하나여야 합니다.", status=400)

    p = Post.objects.create(
        event_id=event_id,
        user_id=request.user_id,
        category=category,
        title=title,
        content=content,
        image_url=image_url,
    )

    p = Post.objects.select_related("user").get(post_id=p.post_id)
    return common_response(True, data=_post_detail(p), message="게시글 작성 성공", status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def post_detail(request, post_id: int):
    if request.method == "PATCH":
        return post_update(request, post_id)
    if request.method == "DELETE":
        return post_delete(request, post_id)
    # 조회수 +1 (동시성 안전)
    updated = Post.objects.filter(post_id=post_id).update(views=F("views") + 1)
    if updated == 0:
        return common_response(False, message="존재하지 않는 게시글입니다.", status=404)
    
    p = Post.objects.select_related("user").get(post_id=post_id)
    return common_response(True, data=_post_detail(p), message="게시글 상세 조회 성공", status=200)


@csrf_exempt
@login_check
@require_http_methods(["PATCH"])
def post_update(request, post_id: int):
    data = _parse_json(request)
    if data is None:
        return common_response(False, message="잘못된 JSON 형식입니다.", status=400)

    try:
        p = Post.objects.get(post_id=post_id)
    except Post.DoesNotExist:
        return common_response(False, message="존재하지 않는 게시글입니다.", status=404)

    if p.user_id != request.user_id:
        return common_response(False, message="수정 권한이 없습니다.", status=403)

    # 부분 수정(PATCH)
    changed = False
    for field in ("category", "title", "content", "image_url"):
        if field in data:
            value = data.get(field)
        
        if field == "category":
            value = normalize_category(value)
            if value is None or value not in ("후기", "질문", "정보"):
                return common_response(False, message="category는 후기/질문/정보 중 하나여야 합니다.", status=400)
        else:
            if isinstance(value, str):
                value = value.strip()

            setattr(p, field, value)
            changed = True

    if not changed:
        return common_response(False, message="수정할 필드가 없습니다.", status=400)

    p.save()
    p = Post.objects.select_related("user").get(post_id=post_id)
    return common_response(True, data=_post_detail(p), message="게시글 수정 성공", status=200)


@csrf_exempt
@login_check
@require_http_methods(["DELETE"])
def post_delete(request, post_id: int):
    try:
        p = Post.objects.get(post_id=post_id)
    except Post.DoesNotExist:
        return common_response(False, message="존재하지 않는 게시글입니다.", status=404)

    if p.user_id != request.user_id:
        return common_response(False, message="삭제 권한이 없습니다.", status=403)

    p.delete()
    return common_response(True, data={"post_id": post_id}, message="게시글 삭제 성공", status=200)



@csrf_exempt
@require_http_methods(["GET", "POST"])
def post_comments_list(request, post_id: int):
    if request.method == "POST":
        return comment_create(request, post_id)

    # GET: 목록 + 페이지네이션
    try:
        page = int(request.GET.get("page") or 1)
        size = int(request.GET.get("size") or 10)
    except ValueError:
        return common_response(False, message="page/size는 정수여야 합니다.", status=400)

    qs = Comment.objects.filter(post_id=post_id).select_related("user").order_by("-created_at", "-comment_id")
    paginator = Paginator(qs, size)
    page_obj = paginator.get_page(page)

    data = {
        "post_id": post_id,
        "comments": [_comment_item(c) for c in page_obj.object_list],
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "page": page_obj.number,
        "size": size,
    }
    return common_response(True, data=data, message="댓글 목록 조회 성공", status=200)


@csrf_exempt
@login_check
@require_POST
def comment_create(request, post_id: int):
    if not Post.objects.filter(post_id=post_id).exists():
        return common_response(False, message="존재하지 않는 게시글입니다.", status=404)

    data = _parse_json(request)
    if data is None:
        return common_response(False, message="잘못된 JSON 형식입니다.", status=400)

    content = (data.get("content") or "").strip()
    if not content:
        return common_response(False, message="content는 필수입니다.", status=400)

    c = Comment.objects.create(
        post_id=post_id,
        user_id=request.user_id,
        content=content,
    )
    c = Comment.objects.select_related("user").get(comment_id=c.comment_id)
    return common_response(True, data=_comment_item(c), message="댓글 작성 성공", status=201)



@csrf_exempt
@login_check
@require_http_methods(["PATCH", "DELETE"])
def comment_detail(request, comment_id: int):
    try:
        c = Comment.objects.get(comment_id=comment_id)
    except Comment.DoesNotExist:
        return common_response(False, message="존재하지 않는 댓글입니다.", status=404)

    if c.user_id != request.user_id:
        return common_response(False, message="권한이 없습니다.", status=403)

    if request.method == "DELETE":
        c.delete()
        return common_response(True, data={"comment_id": comment_id}, message="댓글 삭제 성공", status=200)

    # PATCH
    data = _parse_json(request)
    if data is None:
        return common_response(False, message="잘못된 JSON 형식입니다.", status=400)

    content = (data.get("content") or "").strip()
    if not content:
        return common_response(False, message="content는 필수입니다.", status=400)

    c.content = content
    c.save()
    c = Comment.objects.select_related("user").get(comment_id=comment_id)
    return common_response(True, data=_comment_item(c), message="댓글 수정 성공", status=200)



@csrf_exempt
@login_check
@require_POST
def post_like(request, post_id: int):
    return _toggle_reaction(request, post_id, ReactionType.LIKE)


@csrf_exempt
@login_check
@require_POST
def post_dislike(request, post_id: int):
    return _toggle_reaction(request, post_id, ReactionType.DISLIKE)


def _toggle_reaction(request, post_id: int, target_type: str):
    try:
        with transaction.atomic():
            # 게시글 row lock (카운트 정합성)
            p = Post.objects.select_for_update().get(post_id=post_id)

            r = PostReaction.objects.select_for_update().filter(
                post_id=post_id, user_id=request.user_id
            ).first()

            if r is None:
                # 신규
                PostReaction.objects.create(post_id=post_id, user_id=request.user_id, type=target_type)
                if target_type == ReactionType.LIKE:
                    Post.objects.filter(post_id=post_id).update(like_count=F("like_count") + 1)
                else:
                    Post.objects.filter(post_id=post_id).update(dislike_count=F("dislike_count") + 1)
                new_state = target_type

            else:
                # 토글/스위치
                if r.type == target_type:
                    # 같은 반응이면 취소
                    r.delete()
                    if target_type == ReactionType.LIKE:
                        Post.objects.filter(post_id=post_id).update(like_count=F("like_count") - 1)
                    else:
                        Post.objects.filter(post_id=post_id).update(dislike_count=F("dislike_count") - 1)
                    new_state = None
                else:
                    # dislike -> like 또는 like -> dislike
                    old = r.type
                    r.type = target_type
                    r.save(update_fields=["type"])
                    if old == ReactionType.LIKE:
                        Post.objects.filter(post_id=post_id).update(
                            like_count=F("like_count") - 1,
                            dislike_count=F("dislike_count") + 1,
                        )
                    else:
                        Post.objects.filter(post_id=post_id).update(
                            dislike_count=F("dislike_count") - 1,
                            like_count=F("like_count") + 1,
                        )
                    new_state = target_type

        # 트랜잭션 밖에서 최신 카운트 조회
        p2 = Post.objects.get(post_id=post_id)
        data = {
            "post_id": post_id,
            "reaction": new_state,
            "like": p2.like_count,
            "dislike": p2.dislike_count,
        }
        return common_response(True, data=data, message="리액션 처리 성공", status=200)

    except Post.DoesNotExist:
        return common_response(False, message="존재하지 않는 게시글입니다.", status=404)
    except IntegrityError:
        # 유니크 충돌 등 예외 케이스
        return common_response(False, message="리액션 처리 중 충돌이 발생했습니다.", status=409)



@csrf_exempt
@login_check
@require_POST
def post_report(request, post_id: int):
    if not Post.objects.filter(post_id=post_id).exists():
        return common_response(False, message="존재하지 않는 게시글입니다.", status=404)

    data = _parse_json(request)
    if data is None:
        return common_response(False, message="잘못된 JSON 형식입니다.", status=400)

    reason_category = (data.get("reason_category") or "").strip()
    reason_detail = (data.get("reason_detail") or "").strip() or None

    if not reason_category:
        return common_response(False, message="reason_category는 필수입니다.", status=400)

    try:
        Report.objects.create(
            post_id=post_id,
            user_id=request.user_id,
            reason_category=reason_category,
            reason_detail=reason_detail,
        )
        return common_response(True, data={"post_id": post_id}, message="신고 접수 성공", status=201)
    except IntegrityError:
        return common_response(False, message="이미 신고한 게시글입니다.", status=409)
