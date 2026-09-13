from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.idea_processing import IdeaProcessing


class SQLAlchemyIdeaProcessingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, processing: IdeaProcessing) -> IdeaProcessing:
        self.db.add(processing)
        self.db.flush()
        self.db.refresh(processing)
        return processing

    def list_for_idea(self, idea_id: int) -> list[IdeaProcessing]:
        return self.db.query(IdeaProcessing).filter(IdeaProcessing.idea_id == idea_id).order_by(IdeaProcessing.processed_at.asc()).all()
