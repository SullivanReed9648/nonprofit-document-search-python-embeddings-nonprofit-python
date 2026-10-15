from __future__ import annotations

from math import sqrt
from typing import Any

from nonprofit_search.models import NonprofitDocument, SearchHit, SearchResponse


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class NonprofitSearch:
    def __init__(self, ai: Any, documents: list[NonprofitDocument]) -> None:
        self.ai = ai
        self.documents = documents
        self._vectors: list[list[float]] = []

    def build_index(self) -> None:
        response = self.ai.embeddings.create(
            model="auto",
            input=[f"{doc.title}\n{doc.text}" for doc in self.documents],
        )
        self._vectors = [item.embedding for item in response.data]

    def search(self, query: str, limit: int = 2) -> SearchResponse:
        if len(self._vectors) != len(self.documents):
            raise RuntimeError("Build the document index before searching")

        query_response = self.ai.embeddings.create(model="auto", input=query)
        query_vector = query_response.data[0].embedding
        ranked = sorted(
            zip(self.documents, self._vectors, strict=True),
            key=lambda pair: cosine_similarity(query_vector, pair[1]),
            reverse=True,
        )[:limit]

        hits = [
            SearchHit(
                document_id=document.id,
                kind=document.kind,
                title=document.title,
                score=round(cosine_similarity(query_vector, vector), 4),
            )
            for document, vector in ranked
        ]
        context = "\n\n".join(
            f"[{document.id}] {document.title}\n{document.text}"
            for document, _ in ranked
        )
        completion = self.ai.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer only from the supplied nonprofit records. "
                        "Keep dates and amounts exact, and cite document IDs in brackets."
                    ),
                },
                {"role": "user", "content": f"Question: {query}\n\nRecords:\n{context}"},
            ],
        )
        answer = completion.choices[0].message.content or "No answer was returned."
        return SearchResponse(answer=answer, hits=hits)
