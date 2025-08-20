import logging
from io import BytesIO
from fastapi import HTTPException, status, UploadFile
from minio import Minio
from minio.error import S3Error
from core.config import settings

logger = logging.getLogger(__name__)

class MinioManager:
    def __init__(self, minio_config: dict = None):
        """Khởi tạo FileManager với cấu hình MinIO"""
        self.bucket_name = (
            minio_config.get("bucket") if minio_config else settings.minio_bucket
        )
        self.client = Minio(
            endpoint=settings.minio_endpoint or "localhost:9001",
            access_key=settings.minio_access_key or "minioadmin",
            secret_key=settings.minio_secret_key or "minioadmin",
            secure=False
        )

        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.debug(f"Creating bucket {self.bucket_name}")
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to initialize bucket {self.bucket_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize MinIO bucket: {str(e)}"
            )

    def save_to_minio(self, file: UploadFile, file_stream: BytesIO) -> str:
        """Lưu file lên MinIO và trả về URL của tài liệu"""
        try:
            logger.debug(f"Starting upload of {file.filename} to MinIO")
            file_stream.seek(0)  # Reset vị trí đọc
            object_name = f"origin/{file.filename}"

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=len(file_stream.getvalue()),
                content_type=file.content_type
            )
            logger.info(f"File {file.filename} uploaded to MinIO successfully at {object_name}")

            # Tạo URL đầy đủ
            minio_endpoint = settings.minio_endpoint or "localhost:9001"
            file_url = f"http://{minio_endpoint}/{self.bucket_name}/{object_name}"
            logger.debug(f"Generated file URL: {file_url}")
            return file_url

        except S3Error as e:
            logger.error(f"MinIO error for {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to MinIO: {str(e)}"
            )