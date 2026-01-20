import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.utils import common_response, login_check
from .services import build_object_key, generate_presigned_put_url, make_public_url


def _parse_json(request):
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def _is_allowed_image(content_type: str, filename: str) -> bool:
    ct = (content_type or "").strip().lower()
    fn = (filename or "").strip().lower()

    if not ct.startswith("image/"):
        return False

    # MVP: 최소 허용
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp")
    if not any(fn.endswith(ext) for ext in allowed_ext):
        return False

    # ct(Content Type) 최소 제한
    allowed_ct = ("image/png", "image/jpeg", "image/webp")
    return ct in allowed_ct


@csrf_exempt
@login_check
@require_POST
def presign_upload(request):
    """
    POST /api/uploads/presign
    Body:
      {
        "filename": "a.png",
        "content_type": "image/png"
      }

    Response:
      {
        "upload": {
          "method": "PUT",
          "url": "...presigned..."
        },
        "key": "uploads/..../uuid_a.png",
        "file_url": "https://bucket.s3.region.amazonaws.com/...",
        "expires_in": 300
      }
    """
    data = _parse_json(request)
    if data is None:
        return common_response(False, message="잘못된 JSON 형식입니다.", status=400)

    filename = (data.get("filename") or "").strip()
    content_type = (data.get("content_type") or "").strip()

    if not filename or not content_type:
        return common_response(False, message="filename/content_type는 필수입니다.", status=400)

    if not _is_allowed_image(content_type, filename):
        return common_response(False, message="이미지 업로드는 png/jpg/jpeg/webp만 허용됩니다.", status=400)

    # settings에서 읽기(키 여러 개 fallback 지원)
    bucket = getattr(settings, "S3_UPLOAD_BUCKET", "") or ""
    region = getattr(settings, "AWS_REGION", "") or ""
    prefix = getattr(settings, "S3_UPLOAD_PREFIX", "uploads/")
    expires_in = int(getattr(settings, "S3_PRESIGN_EXPIRES", 300) or 300)
    public_base_url = getattr(settings, "S3_PUBLIC_BASE_URL", None)

    if not bucket or not region:
        return common_response(False, message="S3 설정이 누락되었습니다.(bucket/region)", status=500)

    key = build_object_key(prefix=prefix, user_id=request.user_id, filename=filename)

    try:
        presigned_url = generate_presigned_put_url(
            bucket=bucket,
            region=region,
            key=key,
            expires_in=expires_in,
        )
    except Exception:
        return common_response(False, message="Presigned URL 생성에 실패했습니다.", status=500)

    file_url = make_public_url(bucket=bucket, region=region, key=key, public_base_url=public_base_url)

    resp = {
        "upload": {
            "method": "PUT",
            "url": presigned_url,
            # 서명에 강제하진 않음
            "headers": {"Content-Type": content_type},
        },
        "key": key,
        "file_url": file_url,  # DB에 저장할 “표시용 URL” (image_url)
        "expires_in": expires_in,
    }
    return common_response(True, data=resp, message="Presign 발급 성공", status=200)
