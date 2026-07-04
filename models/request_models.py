from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    session_id: str

    question: str = Field(
        min_length=3,
        max_length=5000
    )