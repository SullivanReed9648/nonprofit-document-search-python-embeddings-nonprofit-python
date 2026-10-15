from types import SimpleNamespace

from nonprofit_search.models import NonprofitDocument
from nonprofit_search.workflow import NonprofitSearch


class FakeEmbeddings:
    def create(self, *, model: str, input: str | list[str]) -> SimpleNamespace:
        if isinstance(input, list):
            vectors = [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]
        else:
            vectors = [[0.95, 0.05]]
        return SimpleNamespace(data=[SimpleNamespace(embedding=vector) for vector in vectors])


class FakeCompletions:
    def create(self, *, model: str, messages: list[dict[str, str]]) -> SimpleNamespace:
        assert "receipt-1042" in messages[1]["content"]
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="The gift was $250 [receipt-1042]."))]
        )


class FakeAI:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddings()
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_receipt_question_selects_receipt_before_other_records() -> None:
    documents = [
        NonprofitDocument(id="receipt-1042", kind="donor_receipt", title="Maya receipt", text="$250 gift"),
        NonprofitDocument(id="volunteer-22", kind="volunteer_reminder", title="Cleanup", text="Meet at 8:30"),
        NonprofitDocument(id="report-2025", kind="campaign_report", title="Pantry report", text="418 households"),
    ]
    search = NonprofitSearch(ai=FakeAI(), documents=documents)
    search.build_index()

    result = search.search("How much did Maya donate?", limit=1)

    assert result.hits[0].kind == "donor_receipt"
    assert result.hits[0].document_id == "receipt-1042"
    assert result.answer == "The gift was $250 [receipt-1042]."

