from notification.models import Notification
from users.models import User
from posts.models import Post
from posts.models import Comment
from events.models import Event

def create_notification(
    user: User,
    type: str,
    message: str,
    relate_url: str = None,
    post: Post = None,
    event: Event = None
):
    """
    user: 알림을 생성할 User 객체
    type: 알림 타입. comment, like, dislike...
    message: 메시지 내용
    relate_url: 클릭하면 이동할 url
    post: 관련 객체
    event: 관련 객체

    -------------------------------------------------------------------------

    1. 내 글에 댓글이 달렸을 때 (COMMENT)
       create_notification(
           user=post.user,
           type=Notification.Type.COMMENT,
           message=f"{request.user.nickname}님이 댓글을 남겼습니다.",
           relate_url=f"/posts/{post.post_id}#comment-{comment.comment_id}", # 앵커 활용
           post=post
       )

    2. 내 글에 좋아요가 눌렸을 때 (POST_LIKE)
       create_notification(
           user=post.user,
           type=Notification.Type.POST_LIKE,
           message=f"{request.user.nickname}님이 회원님의 글을 좋아합니다.",
           relate_url=f"/posts/{post.post_id}",
           post=post
       )

    3. 관심 공연 정보가 업데이트되었을 때 (EVENT)
       create_notification(
           user=target_user,
           type=Notification.Type.EVENT,
           message="찜한 공연 '시카고'의 티켓 오픈일이 다가옵니다!",
           relate_url=f"/events/{event.event_id}",
           event=event
       )

    4. 레벨업 등 시스템 공지 (NOTICE) - post/event 없음
       create_notification(
           user=user,
           type=Notification.Type.NOTICE,
           message=f"축하합니다! Lv.{user.level}로 레벨업 하셨습니다! 🎉",
           relate_url="/mypage"
       )
    -------------------------------------------------------------------------
    """
    try:
        Notification.objects.create(
            user=user,
            type=type,
            message=message,
            relate_url=relate_url,
            post=post,
            event=event,
            is_read=False
        )
    except Exception as e:
        print(f"알림 생성 실패: {e}")