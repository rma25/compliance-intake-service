"""Document storage: an interface (Protocol) with a local and an S3 implementation.

For a C# dev: `Protocol` is a structural interface. Any class with a matching
`save(...)` signature satisfies `DocumentStore` — no explicit `implements`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class DocumentStore(Protocol):
    def save(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str: ...


class LocalDocumentStore:
    """Writes documents to a local directory. Returns a file:// URI."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path.resolve().as_uri()


class S3DocumentStore:
    """AWS-backed store. Lazy-imports boto3 so the local path needs no AWS deps."""

    def __init__(self, bucket: str, region: str = "us-east-1") -> None:
        import boto3  # lazy import: only required when this backend is selected

        self._bucket = bucket
        self._client = boto3.client("s3", region_name=region)

    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{self._bucket}/{key}"
