from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.idea_note import IdeaNote


class SQLAlchemyIdeaNoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, note: IdeaNote) -> IdeaNote:
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def list_for_idea(self, idea_id: int) -> list[IdeaNote]:
        return self.db.query(IdeaNote).filter(IdeaNote.idea_id == idea_id).order_by(IdeaNote.created_at.asc()).all()
