import io

import magic
from core.config import MediaType, minio_client, settings
from fastapi import HTTPException

# from markitdown import MarkItDown


# ------------------------------------------------------------------------
# md = MarkItDown(enable_plugins=False)


async def detect_mime_type(file_bytes: bytes) -> str:
    """
    Detects the MIME type of a bytes object.

    Args:
        file_bytes: A bytes object containing the file data.

    Returns:
        str: The detected MIME type, or 'application/octet-stream' if unknown.
    """
    # Use the first 2048 bytes for detection
    mime_type = magic.from_buffer(file_bytes[:2048], mime=True)
    return mime_type


async def process_file(content: bytes, object_name: str, content_type: str) -> str:

    mime_type = await detect_mime_type(content)

    # Accept images and common document types
    allowed_types = [
        "image/",
        # "text/plain",
        "application/pdf",
        # "application/msword",
        # "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # "application/vnd.ms-excel",
        # "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        # "application/vnd.ms-powerpoint",
        # "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ]
    if mime_type and mime_type.startswith("image/"):
        # Case 1: Image file

        await minio_client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            io.BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

        return MediaType.image.name

    elif mime_type and mime_type in allowed_types[1:]:
        # Case 2: Remaining allowed types (documents)
        # await minio_client.put_object(
        #     settings.MINIO_BUCKET,
        #     object_name,
        #     io.BytesIO(content),
        #     length=len(content),
        #     content_type=content_type,
        # )
        # content_text = md.convert(io.BytesIO(content))
        return MediaType.document.name

    else:
        # Case 3: Out of scope
        raise HTTPException(
            status_code=400, detail=f"File type '{mime_type}' is not supported"
        )
