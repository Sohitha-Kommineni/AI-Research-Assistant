from datetime import datetime
from pathlib import Path

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.models import Document, DocumentChunk, Project
from app.routers.auth import get_current_user
from app.schemas import DocumentOut, DocumentTextResponse, IngestUrlRequest
from app.services.ingestion import build_chunks, embed_chunks, parse_pdf, parse_text, parse_url
from app.utils.files import save_upload


router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])
logger = logging.getLogger(__name__)


def _persist_chunks(db: Session, project_id: int, document: Document, chunks: list[dict]) -> None:
    for chunk in chunks:
        db.add(
            DocumentChunk(
                document_id=document.id,
                project_id=project_id,
                content=chunk["content"],
                embedding=chunk.get("embedding"),
                page_number=chunk.get("page_number"),
            )
        )


def _ingest_document(
    project_id: int, document_id: int, source_path: Path | None, raw_text: str | None
) -> None:
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return

        if document.doc_type == "pdf" and source_path:
            text, pages = parse_pdf(str(source_path))
        elif document.doc_type == "text" and raw_text is not None:
            text, pages = parse_text(raw_text)
        elif document.doc_type == "url" and document.source_url:
            text, pages = parse_url(document.source_url)
        else:
            document.status = "failed"
            db.commit()
            return

        chunks = build_chunks(pages)
        if not chunks:
            document.text_excerpt = text[:5000]
            document.metadata_json = {
                "page_count": len(pages),
                "error": "No extractable text found in this document.",
            }
            document.status = "failed"
            db.commit()
            return

        chunks = embed_chunks(chunks)
        _persist_chunks(db, project_id, document, chunks)
        document.text_excerpt = text[:5000]
        document.metadata_json = {"page_count": len(pages)}
        document.status = "ready"
        db.commit()
    except Exception as exc:
        if document:
            document.status = "failed"
            document.metadata_json = {"error": str(exc)}
            db.commit()
        logger.exception("Failed to ingest document %s", document_id)
    finally:
        db.close()


@router.get("", response_model=list[DocumentOut])
def list_documents(
    project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> list[DocumentOut]:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Document).filter(Document.project_id == project_id).order_by(Document.created_at.desc()).all()


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> DocumentOut:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    ext = (file.filename or "").lower().split(".")[-1]
    if ext not in {"pdf", "txt"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    doc_type = "pdf" if ext == "pdf" else "text"
    document = Document(project_id=project_id, name=file.filename or "document", doc_type=doc_type)
    db.add(document)
    db.commit()
    db.refresh(document)

    source_path = save_upload(file.file, file.filename or f"document_{document.id}.{ext}")
    raw_text = None
    if doc_type == "text":
        raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
    background_tasks.add_task(_ingest_document, project_id, document.id, source_path, raw_text)
    project.last_activity_at = datetime.utcnow()
    db.commit()
    return document


@router.post("/url", response_model=DocumentOut)
def ingest_url(
    project_id: int,
    payload: IngestUrlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> DocumentOut:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    document = Document(
        project_id=project_id, name=payload.url, doc_type="url", source_url=payload.url
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    background_tasks.add_task(_ingest_document, project_id, document.id, None, None)
    project.last_activity_at = datetime.utcnow()
    db.commit()
    return document


@router.get("/{document_id}/text", response_model=DocumentTextResponse)
def get_document_text(
    project_id: int, document_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> DocumentTextResponse:
    document = (
        db.query(Document)
        .join(Project, Project.id == Document.project_id)
        .filter(Project.user_id == user.id, Document.id == document_id, Document.project_id == project_id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentTextResponse(document_id=document.id, text=document.text_excerpt or "", metadata=document.metadata_json)
