import logging
import os
import uuid
from io import BytesIO
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException, status
from minio import Minio
from minio.error import S3Error
from openai import OpenAI
from minio import Minio
from bunnet import PydanticObjectId
from core.config import settings , openai_client , logger , minio_client
# Load biến môi trường từ file .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger = logging.getLogger(__name__)

class MinioManager:
    def __init__(self, minio_config: dict):
        """Khởi tạo FileManager với cấu hình MinIO"""
        self.client = minio_client
        self.bucket_name = (
            minio_config.get("bucket") if minio_config else settings.minio_bucket
        )
    async def save_to_minio(self, file: UploadFile, file_stream: BytesIO) -> str:
        """Lưu file lên MinIO và trả về URL hoặc path của tài liệu"""
        try:
            file_stream.seek(0)  # Reset vị trí đọc

            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            object_name = f"origin/{file.filename}"
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=len(file_stream.getvalue()),
                content_type=file.content_type
            )
            logger.info(f"File {file.filename} uploaded to MinIO successfully")

            # Tạo URL đầy đủ (thay đổi endpoint theo cấu hình MinIO của bạn)
            # minio_endpoint = "http://61.28.231.71:9001/browser"  
            file_path = f"{self.bucket_name}/{file.filename}"
            # file_url = f"{minio_endpoint}/{file_path}"
            return file_path  # Ví dụ: "http://localhost:9000/documents/report.pdf"

        except S3Error as e:
            logger.error(f"MinIO error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file to MinIO")



