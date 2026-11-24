import io
import hashlib
from typing import Tuple

import boto3
from botocore.client import Config
from PIL import Image

from app.config import settings

_s3 = None


def _client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        _ensure_bucket()
    return _s3


def _ensure_bucket():
    try:
        _s3.head_bucket(Bucket=settings.MINIO_BUCKET)
    except Exception:
        _s3.create_bucket(Bucket=settings.MINIO_BUCKET)


def upload_screenshot(data: bytes, key: str) -> Tuple[str, str, str]:
    """Upload full screenshot + generate thumbnail.

    Returns (storage_key, thumbnail_key, sha256_hex).
    """
    sha256 = hashlib.sha256(data).hexdigest()

    # Resize to max 1280×800
    img = Image.open(io.BytesIO(data))
    img.thumbnail((1280, 800), Image.LANCZOS)
    full_buf = io.BytesIO()
    img.save(full_buf, format="PNG", optimize=True)
    full_buf.seek(0)

    # Thumbnail at 320×200
    thumb = img.copy()
    thumb.thumbnail((320, 200), Image.LANCZOS)
    thumb_buf = io.BytesIO()
    thumb.save(thumb_buf, format="JPEG", quality=70)
    thumb_buf.seek(0)

    thumb_key = key.replace("screenshots/", "thumbnails/").replace(".png", ".jpg")

    client = _client()
    client.put_object(Bucket=settings.MINIO_BUCKET, Key=key, Body=full_buf, ContentType="image/png")
    client.put_object(Bucket=settings.MINIO_BUCKET, Key=thumb_key, Body=thumb_buf, ContentType="image/jpeg")

    return key, thumb_key, sha256


def get_presigned_url(key: str, expires: int = 3600) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.MINIO_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(key: str) -> None:
    _client().delete_object(Bucket=settings.MINIO_BUCKET, Key=key)
