import logging
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import uuid

from src.api.constants import ALLOWED_EXTENSIONS
from src.api.dependencies.services import config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    allowed_exts = [v.value for v in ALLOWED_EXTENSIONS]

    if not file.filename:  # Just to satisfy mypy
        raise HTTPException(status_code=400, detail="Filename is missing.")

    ext = os.path.splitext(file.filename)[-1].lower()[1:]

    if ext not in allowed_exts:
        logger.warning("File upload initated with unknown extension. Raising Exception")
        raise HTTPException(status_code=400, detail=f"Only {",".join(allowed_exts)} files allowed.")

    # Check file limit
    existing_files = os.listdir(config.documents_folder)
    if len(existing_files) >= config.max_upload_files:
        logger.warning("File container is full. Max number of allowed uploads reached.")
        raise HTTPException(status_code=400, detail="Document folder is full.")

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(config.documents_folder, unique_name)

    # Save file
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"status": "success", "filename": unique_name}


@router.delete("/upload/clear")
async def clear_uploaded_documents():
    folder = config.documents_folder
    count = 0
    for f in os.listdir(folder):
        try:
            os.remove(os.path.join(folder, f))
            count += 1
        except Exception as e:
            logger.warning("Could not delete %s: %s", f, e)

    return {"status": "cleared", "deleted_files": count}
