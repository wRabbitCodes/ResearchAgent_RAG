import logging
import os

from fastapi.responses import JSONResponse
from fastapi import APIRouter, BackgroundTasks, Query, status, HTTPException

from src.ingestion.document_ingestor import DocumentIngestor
from src.api.dependencies.services import config, vectorstore

import shutil


logger = logging.getLogger(__name__)

router = APIRouter()


# TODO: Automate with schedulers.
@router.get("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def start_ingestion(
    background_tasks: BackgroundTasks,
    overwrite: bool = Query(default=False, description="If true, will overwrite existing chunks."),
):
    folder_path = config.documents_folder

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"Folder path '{folder_path}' does not exist or is not a directory.",
            },
        )

    def ingestion_task():
        try:
            ingestor = DocumentIngestor(
                vectorstore=vectorstore,
            )

            if vectorstore.count() > 0:
                if overwrite:
                    logger.info("[Ingestor] Overwriting existing documents for ingestion")
                else:
                    logger.info("[Ingestor] Performing incremental upsert")
            else:
                logger.info("[Ingestor] Performing initial ingestion")

            ingestor.ingest(folder_path, overwrite_existing=overwrite)
            logger.info("[Ingestor] Ingestion completed successfully")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("[Ingestor] Ingestion failed: %s", e)

    background_tasks.add_task(ingestion_task)

    return {
        "status": "started",
        "overwrite": overwrite,
        "message": f"Ingestion started in background for folder: {folder_path}",
    }


@router.delete("/chroma/clear")
async def clear_chromadb_storage():
    chroma_path = config.chroma_db_path

    if not os.path.exists(chroma_path):
        logger.warning("DB folders not present.")
        raise HTTPException(status_code=404, detail="Chroma DB path not found.")

    try:
        shutil.rmtree(chroma_path)
        os.makedirs(chroma_path, exist_ok=True)
        logger.info("[Chroma] Cleared ChromaDB folder at %s", chroma_path)
        return {"status": "success", "message": f"Cleared ChromaDB at {chroma_path}"}
    except Exception as e:
        logger.error("[Chroma] Failed to clear ChromaDB: %s", e)
        raise HTTPException(status_code=500, detail="Failed to clear ChromaDB folder.")
