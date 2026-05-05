"""
Object storage service for cluster deployment.

Supports S3, MinIO, and Aliyun OSS for storing PDFs and other files.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ObjectStorageService:
    """S3-compatible object storage service."""

    def __init__(self):
        self.enabled = False
        self.provider = "minio"
        self.bucket_name = "paper-agent"
        self._client = None

    async def init(self):
        """Initialize object storage client."""
        from backend.config.cluster_settings import cluster_settings
        if not cluster_settings.storage.enabled:
            logger.info("Object storage disabled, using local filesystem")
            return

        self.provider = cluster_settings.storage.provider
        self.bucket_name = cluster_settings.storage.bucket_name

        try:
            if self.provider in ("minio", "s3"):
                import boto3
                from botocore.config import Config

                config = Config(
                    s3={"addressing_style": "path"},
                    retries={"max_attempts": 3, "mode": "standard"},
                )

                self._client = boto3.client(
                    "s3",
                    endpoint_url=cluster_settings.storage.endpoint if self.provider == "minio" else None,
                    aws_access_key_id=cluster_settings.storage.access_key,
                    aws_secret_access_key=cluster_settings.storage.secret_key,
                    region_name=cluster_settings.storage.region,
                    config=config,
                )

                # Ensure bucket exists
                try:
                    self._client.head_bucket(Bucket=self.bucket_name)
                except Exception:
                    self._client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")

                self.enabled = True
                logger.info(f"Object storage connected: {self.provider}")

            elif self.provider == "oss":
                # Aliyun OSS
                try:
                    from oss2 import Auth, Bucket, Service
                    auth = Auth(
                        cluster_settings.storage.access_key,
                        cluster_settings.storage.secret_key
                    )
                    endpoint = cluster_settings.storage.endpoint
                    self._client = Bucket(auth, endpoint, self.bucket_name)
                    self.enabled = True
                    logger.info(f"OSS connected: {self.bucket_name}")
                except ImportError:
                    logger.warning("oss2 not installed. OSS storage unavailable.")

        except Exception as e:
            logger.warning(f"Object storage connection failed: {e}. Using local storage.")

    def _get_key(self, path: str, prefix: str = "pdfs/") -> str:
        return f"{prefix}{path}"

    async def upload_file(
        self,
        local_path: str,
        remote_path: Optional[str] = None,
        content_type: str = "application/pdf",
    ) -> Optional[str]:
        """Upload a file to object storage."""
        if not self.enabled:
            return None

        remote_path = remote_path or Path(local_path).name
        key = self._get_key(remote_path)

        try:
            if self.provider in ("minio", "s3"):
                self._client.upload_file(
                    local_path,
                    self.bucket_name,
                    key,
                    ExtraArgs={"ContentType": content_type},
                )
            elif self.provider == "oss":
                self._client.put_object_from_file(key, local_path)

            logger.info(f"Uploaded to object storage: {key}")
            return key
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    async def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/pdf",
    ) -> Optional[str]:
        """Upload bytes data."""
        if not self.enabled:
            return None

        full_key = self._get_key(key)
        try:
            if self.provider in ("minio", "s3"):
                from io import BytesIO
                self._client.upload_fileobj(
                    BytesIO(data),
                    self.bucket_name,
                    full_key,
                    ExtraArgs={"ContentType": content_type},
                )
            elif self.provider == "oss":
                self._client.put_object(full_key, data)

            return full_key
        except Exception as e:
            logger.error(f"Upload bytes failed: {e}")
            return None

    async def download_file(self, key: str, local_path: str) -> bool:
        """Download a file from object storage."""
        if not self.enabled:
            return False

        try:
            if self.provider in ("minio", "s3"):
                self._client.download_file(self.bucket_name, key, local_path)
            elif self.provider == "oss":
                self._client.get_object_to_file(key, local_path)
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    async def delete_file(self, key: str) -> bool:
        """Delete a file from object storage."""
        if not self.enabled:
            return False

        try:
            if self.provider in ("minio", "s3"):
                self._client.delete_object(Bucket=self.bucket_name, Key=key)
            elif self.provider == "oss":
                self._client.delete_object(key)
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a presigned URL for direct access."""
        if not self.enabled:
            return None

        try:
            if self.provider in ("minio", "s3"):
                url = self._client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
        return None

    async def list_files(self, prefix: str = "pdfs/") -> list:
        """List files with prefix."""
        if not self.enabled:
            return []

        try:
            if self.provider in ("minio", "s3"):
                paginator = self._client.get_paginator("list_objects_v2")
                pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
                files = []
                for page in pages:
                    for obj in page.get("Contents", []):
                        files.append({
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"].isoformat(),
                        })
                return files
        except Exception as e:
            logger.error(f"List files failed: {e}")
        return []


# Global storage instance
storage = ObjectStorageService()
