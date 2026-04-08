"""Data upload endpoint for dataloader integration."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

router = APIRouter()


class UploadResponse(BaseModel):
    filename: str
    size: int
    status: str


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing by the dataloader."""
    allowed_types = {".pdf", ".csv", ".json", ".txt", ".xlsx"}
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {allowed_types}",
        )

    # Save to temp location for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="/tmp") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    return UploadResponse(
        filename=file.filename or "unknown",
        size=len(content),
        status=f"saved to {tmp_path} — ready for ingestion",
    )
