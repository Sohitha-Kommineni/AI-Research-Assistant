from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document, Project
from app.routers.auth import get_current_user
from app.schemas import ProjectCreate, ProjectOut


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> ProjectOut:
    project = Project(user_id=user.id, name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        last_activity_at=project.last_activity_at,
        document_count=0,
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[ProjectOut]:
    projects = (
        db.query(Project, func.count(Document.id))
        .outerjoin(Document, Document.project_id == Project.id)
        .filter(Project.user_id == user.id)
        .group_by(Project.id)
        .order_by(Project.last_activity_at.desc())
        .all()
    )
    response = []
    for project, count in projects:
        response.append(
            ProjectOut(
                id=project.id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                last_activity_at=project.last_activity_at,
                document_count=count,
            )
        )
    return response


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> ProjectOut:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    count = db.query(Document).filter(Document.project_id == project.id).count()
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        last_activity_at=project.last_activity_at,
        document_count=count,
    )


@router.post("/{project_id}/touch")
def touch_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> dict:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.last_activity_at = datetime.utcnow()
    db.commit()
    return {"status": "ok"}
