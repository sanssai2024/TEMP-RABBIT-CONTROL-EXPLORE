from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.idea import Idea, IdeaDecision, IdeaStatus
from app.models.idea_processing import IdeaProcessingMode
from app.repositories.idea_repository import SQLAlchemyIdeaRepository
from app.schemas.ai_processing import AIProcessingResult
from app.services.ai_service import AIConfigurationError, AIProcessingValidationError, AIProviderError, AIService, OpenAICompatibleProvider
from app.services.idea_persistence_service import IdeaPersistenceService
from app.services.idea_processing_service import IdeaProcessingService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_ai_service() -> AIService:
    provider = OpenAICompatibleProvider(api_key=settings.ai_api_key, base_url=settings.ai_base_url)
    return AIService(provider=provider, model_name=settings.ai_model, api_key=settings.ai_api_key)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ideas")
def list_ideas(request: Request, db: Session = Depends(get_db)) -> Any:
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/templates")
    service = IdeaPersistenceService(db)
    ideas = service.list_ideas()
    return templates.TemplateResponse("ideas.html", {"request": request, "ideas": ideas})


@router.get("/ideas/new")
def new_idea(request: Request) -> Any:
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("idea_form.html", {"request": request, "modes": ["CONTROL", "EXPLORE"]})


@router.post("/ideas")
def create_idea(request: Request, original_idea: str = Form(...), mode: str = Form(...), db: Session = Depends(get_db)) -> Any:
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/templates")
    if not original_idea or not original_idea.strip():
        return templates.TemplateResponse(
            "idea_form.html",
            {"request": request, "error": "Please provide an idea before submitting.", "modes": ["CONTROL", "EXPLORE"]},
            status_code=400,
        )

    try:
        selected_mode = IdeaProcessingMode(mode)
    except ValueError:
        return templates.TemplateResponse(
            "idea_form.html",
            {"request": request, "error": "Please choose a valid processing mode.", "modes": ["CONTROL", "EXPLORE"]},
            status_code=400,
        )

    service = IdeaPersistenceService(db)
    idea = service.create_idea(original_idea)

    try:
        processing_service = IdeaProcessingService(db, get_ai_service())
        processing_service.process_idea(idea, selected_mode)
    except AIProviderError as exc:
        logger.error("AI failure layer=application processing error_type=%s message=%s", type(exc).__name__, str(exc)[:500])
        return templates.TemplateResponse(
            "idea_detail.html",
            {
                "request": request,
                "idea": idea,
                "error": "RABBIT could not process this idea. Please try again.",
                "processing": None,
                "notes": service.list_notes_for_idea(idea.id),
                "processings": service.list_processings_for_idea(idea.id),
            },
            status_code=400,
        )
    except Exception as exc:
        logger.exception("AI failure layer=persistence or application error_type=%s", type(exc).__name__)
        return templates.TemplateResponse(
            "idea_detail.html",
            {
                "request": request,
                "idea": idea,
                "error": "RABBIT could not process this idea. Please try again.",
                "processing": None,
                "notes": service.list_notes_for_idea(idea.id),
                "processings": service.list_processings_for_idea(idea.id),
            },
            status_code=400,
        )

    return RedirectResponse(f"/ideas/{idea.id}", status_code=303)


@router.get("/ideas/{idea_id}")
def show_idea(idea_id: int, request: Request, db: Session = Depends(get_db)) -> Any:
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/templates")
    service = IdeaPersistenceService(db)
    try:
        idea = service.get_idea(idea_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Idea not found")

    processings = service.list_processings_for_idea(idea_id)
    notes = service.list_notes_for_idea(idea_id)
    latest = processings[-1] if processings else None
    result = None
    if latest:
        result = AIProcessingResult.model_validate(latest.structured_result_json)

    return templates.TemplateResponse(
        "idea_detail.html",
        {
            "request": request,
            "idea": idea,
            "processings": processings,
            "notes": notes,
            "latest": latest,
            "result": result,
            "error": None,
        },
    )


@router.post("/ideas/{idea_id}/notes")
def add_note(idea_id: int, note_text: str = Form(...), db: Session = Depends(get_db)) -> Any:
    service = IdeaPersistenceService(db)
    try:
        service.add_note(idea_id, note_text)
    except ValueError:
        raise HTTPException(status_code=400, detail="Note text cannot be blank")
    return RedirectResponse(f"/ideas/{idea_id}", status_code=303)


@router.post("/ideas/{idea_id}/status")
def update_status(idea_id: int, status: str = Form(...), db: Session = Depends(get_db)) -> Any:
    service = IdeaPersistenceService(db)
    try:
        idea = service.get_idea(idea_id)
        idea.status = IdeaStatus(status).value
        db.add(idea)
        db.commit()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid idea status")
    return RedirectResponse(f"/ideas/{idea_id}", status_code=303)


@router.post("/ideas/{idea_id}/reprocess")
def reprocess_idea(idea_id: int, mode: str = Form(...), db: Session = Depends(get_db)) -> Any:
    service = IdeaPersistenceService(db)
    idea = service.get_idea(idea_id)
    try:
        selected_mode = IdeaProcessingMode(mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid processing mode")

    try:
        processing_service = IdeaProcessingService(db, get_ai_service())
        processing_service.process_idea(idea, selected_mode)
    except AIProviderError as exc:
        logger.error("AI failure layer=application processing error_type=%s message=%s", type(exc).__name__, str(exc)[:500])
        raise HTTPException(status_code=400, detail="RABBIT could not process this idea. Please try again.")
    except Exception as exc:
        logger.exception("AI failure layer=persistence or application error_type=%s", type(exc).__name__)
        raise HTTPException(status_code=400, detail="RABBIT could not process this idea. Please try again.")

    return RedirectResponse(f"/ideas/{idea_id}", status_code=303)
