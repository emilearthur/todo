"""All functions to handle models of notes summarize."""


from app.models.core import CoreModel, DateTimeModelMixin, IDModelMixin


class NoteBase(CoreModel):
    """All common characteristics of Notes."""

    pass


class NoteCreate(NoteBase):
    """Create notes."""

    todo_id: int
    notes_summary: str


class NoteInDB(IDModelMixin, DateTimeModelMixin, NoteBase):
    """summarized note coming from DB."""

    todo_id: int
    notes_summary: str


class NotePublic(NoteInDB):
    """Note to public."""

    pass
