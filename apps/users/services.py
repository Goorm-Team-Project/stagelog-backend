import math
from users.models import User
from notifications.models import Notification
from notifications.services import create_notification
from django.db import transaction, models

""" 사용 예시

from users.services import apply_user_exp, ExpPolicy

apply_user_exp(request.user, ExpPolicy.Post) 

와 같이 단독으로 사용하거나 (DB에 적용됨)

아래처럼 return 값을 적절히 활용해서 프론트에 추가적인 데이터를 전달

exp_result = apply_user_exp(request.user, ExpPolicy.POST)

    # 응답 데이터 구성
    p = Post.objects.select_related("user").get(post_id=p.post_id)
    response_data = _post_detail(p)
    
    # ✅ 경험치 결과 추가
    response_data['exp_result'] = exp_result

    # 메시지 설정
    message = "게시글 작성 성공"
    if exp_result['leveled_up']:
        message += f" (축! Lv.{exp_result['current_level']} 달성!)"

    return common_response(True, data=response_data, message=message, status=201)

"""


class ExpPolicy(models.IntegerChoices):
    POST = 50
    COMMENT = 10

def user_exp_calculator(base_exp, user_level, decay_factor=0.1):
    """
    base_exp : 활동으로 획득하는 점수(글쓰기, 댓글 ...)
    user_level : 현재 유저의 레벨
    decay_factor : 경험치 획득 감소 계수
    """
    if user_level < 1:
        user_level = 1
    
    multiplier = 1 / (1 + (decay_factor * (user_level - 1)))
    exp = base_exp * multiplier

    return max(1, round(exp))

#transaction.atomic 으로 함수 전체 성공 보장
@transaction.atomic
def apply_user_exp(user: User, type: ExpPolicy):
    base_exp = type.value

    gained_exp = user_exp_calculator(base_exp, user.level)

    user.exp += gained_exp
    is_levelup = False

    # 다중 레벨업 계산
    while True:
        if user.exp < 100:
            break
        user.exp -= 100
        user.level += 1
        is_levelup = True

    user.save()

    if is_levelup:
        create_notification(
            user=user,
            type=Notification.Type.NOTICE,
            message=f"레벨이 {user.level} 로 올랐습니다!",
            relate_url="/api/users/me"
        )

    return {
        "success": True,
        "level_up": is_levelup,
        "current_level": user.level,
        "gained_exp": gained_exp
    }