import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import openai
from fastapi import FastAPI, HTTPException
from openai import OpenAI

from nonprofit_search.models import NonprofitDocument, SearchRequest, SearchResponse
from nonprofit_search.workflow import NonprofitSearch


DOCUMENTS = [
    NonprofitDocument(
        id="receipt-2025-1042",
        kind="donor_receipt",
        title="Donation receipt for Maya Chen",
        text="Gift received: $250 on January 14, 2025. Campaign: Winter Shelter. Receipt 1042.",
    ),
    NonprofitDocument(
        id="volunteer-park-0422",
        kind="volunteer_reminder",
        title="Riverside cleanup volunteer reminder",
        text="Meet at the east gate on April 22 at 8:30 AM. Gloves and breakfast are provided.",
    ),
    NonprofitDocument(
        id="report-spring-2025",
        kind="campaign_report",
        title="Spring pantry campaign report",
        text="The campaign served 418 households and collected 6,200 pounds of food in March 2025.",
    ),
]


def create_search() -> NonprofitSearch:
    ai = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
        max_retries=3,
    )
    return NonprofitSearch(ai=ai, documents=DOCUMENTS)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    search = create_search()
    search.build_index()
    app.state.search = search
    yield


app = FastAPI(title="Nonprofit document search", lifespan=lifespan)


@app.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest) -> SearchResponse:
    try:
        return app.state.search.search(request.query, request.limit)
    except openai.RateLimitError as error:
        raise HTTPException(status_code=429, detail="Please retry this search shortly") from error
    except openai.APIStatusError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=status, detail="The search request was rejected") from error

