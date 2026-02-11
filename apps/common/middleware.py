import logging
from django.http import JsonResponse
from apps.common.utils import common_response, get_client_ip
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AutoBanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        self.LIMIT_WINDOW = 60  # 감시 시간
        self.MAX_REQUESTS = 100 # 허용 횟수
        self.BLOCK_TIME = 3600 # 차단 시간

    def __call__(self, request):
        ip = get_client_ip(request)

        if cache.get(f"block_{ip}"):
            logger.warning(f"차단된 IP 입니다: {ip}")
            return common_response(success=False, message="차단된 IP 입니다.", status=403)
        
        request_key = f"req_count_{ip}"

        current_count = cache.get_or_set(request_key, 0, timeout=self.LIMIT_WINDOW)

        cache.incr(request_key)

        if current_count > self.MAX_REQUESTS:
            cache.set(f"block_{ip}", "banned", timeout=self.BLOCK_TIME)

            logger.error(f"자동으로 IP가 밴 되었습니다: {ip}. (Too many requests)")
            return common_response(success=False, message="너무 많은 요청으로 차단되었습니다.", status=429)
        
        response = self.get_response(request)
        return response
    
