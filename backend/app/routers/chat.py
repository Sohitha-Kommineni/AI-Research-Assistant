import json
import time
from datetime import datetime
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChatMessage, Project
from app.routers.auth import get_current_user
from app.schemas import ChatMessageOut, ChatRequest, ChatResponse
from app.services.rag import answer_question


router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])


@router.get("", response_model=list[ChatMessageOut])
def get_history(
    project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> list[ChatMessageOut]:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return messages


@router.post("", response_model=ChatResponse)
def chat(
    project_id: int, payload: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> ChatResponse:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    answer, citations, used_chunks = answer_question(db, project, user.id, payload.question)
    project.last_activity_at = datetime.utcnow()
    db.commit()
    return ChatResponse(answer=answer, citations=citations, used_chunks=used_chunks)


@router.post("/stream")
def chat_stream(
    project_id: int, payload: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> StreamingResponse:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    def event_stream() -> Generator[str, None, None]:
        answer, citations, used_chunks = answer_question(db, project, user.id, payload.question)
        project.last_activity_at = datetime.utcnow()
        db.commit()
        for token in answer.split(" "):
            data = json.dumps({"type": "token", "value": token + " "})
            yield f"data: {data}\n\n"
            time.sleep(0.02)
        final_payload = json.dumps(
            {"type": "done", "citations": [c.dict() for c in citations], "used_chunks": used_chunks}
        )
        yield f"data: {final_payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
