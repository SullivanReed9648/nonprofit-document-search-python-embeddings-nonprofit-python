from typing import Literal

from pydantic import BaseModel, Field


DocumentKind = Literal["donor_receipt", "volunteer_reminder", "campaign_report"]


class NonprofitDocument(BaseModel):
    id: str
    kind: DocumentKind
    title: str
    text: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    limit: int = Field(default=2, ge=1, le=3)


class SearchHit(BaseModel):
    document_id: str
    kind: DocumentKind
    title: str
    score: float


class SearchResponse(BaseModel):
    answer: str
    hits: list[SearchHit]

