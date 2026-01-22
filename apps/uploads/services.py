import re
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config


_FILENAME_SAFE_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_filename(filename: str) -> str:
    name = (filename or "").strip()
    if not name:
        return "file"

    # 경로 제거
    name = name.split("/")[-1].split("\\")[-1]

    # 너무 긴 파일명 방지
    name = name[:120]

    # 안전 문자만 남기기
    name = _FILENAME_SAFE_RE.sub("_", name).strip("._")
    return name or "file"


def build_object_key(prefix: str, user_id: int, filename: str) -> str:
    # prefix 정규화
    p = (prefix or "uploads/").strip()
    if not p.endswith("/"):
        p += "/"

    safe = _safe_filename(filename)
    now = datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")
    uid = uuid.uuid4().hex
    return f"{p}{user_id}/{date_path}/{uid}_{safe}"


def make_public_url(bucket: str, region: str, key: str, public_base_url: str | None = None) -> str:
    if public_base_url:
        base = public_base_url.rstrip("/")
        return f"{base}/{key}"
    # virtual-hosted–style
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def generate_presigned_put_url(
    *,
    bucket: str,
    region: str,
    key: str,
    expires_in: int,
) -> str:
    # role 기반 기본 credential chain 사용(EC2 IAM Role)
    client = boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version="s3v4"),
    )

    return client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
        },
        ExpiresIn=expires_in,
        HttpMethod="PUT",
    )
