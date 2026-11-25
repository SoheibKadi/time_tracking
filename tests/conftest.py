"""Root conftest: sets environment variables and sys.path BEFORE any app imports."""
import os
import sys

# Minimal env required by pydantic-settings — values are overridden per-test
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-only-not-for-production")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("MINIO_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("MINIO_BUCKET", "test")
os.environ.setdefault("ALLOW_REGISTRATION", "true")
os.environ.setdefault("SMTP_HOST", "")

_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(_root, "backend"))
sys.path.insert(0, os.path.join(_root, "agent"))
