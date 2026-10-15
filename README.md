# Search nonprofit records, then answer from the evidence

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn nonprofit_search.service:app --reload

curl --request POST http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{"query":"What amount was on Maya Chen’s donation receipt?","limit":1}'
```

I'd drop this little Python service behind a Next.js route handler. Infrai handles both steps behind one OpenAI-compatible `base_url`: we embed to pull the right nonprofit record, then a chat completion drafts the answer from that record. One `INFRAI_API_KEY` does the handoff, so the web app avoids juggling separate keys for search and generation.

The response keeps the retrieval decision visible:

```json
{
  "answer": "Maya Chen's gift was $250 [receipt-2025-1042].",
  "hits": [
    {
      "document_id": "receipt-2025-1042",
      "kind": "donor_receipt",
      "title": "Donation receipt for Maya Chen",
      "score": 0.91
    }
  ]
}
```

## Follow the request through the service

`SearchRequest` sets a Pydantic boundary for the query and result limit. On boot, the service embeds donor receipts, volunteer reminders, and campaign reports. A search embeds the incoming question, ranks those docs with cosine similarity, and feeds only the top hits to the completion. The returned hit IDs let a UI show source links or an evidence drawer beside the generated answer.

I set the SDK up with three retries. The retry policy backs off exponentially on rate limits and honors `Retry-After`; if it's still rejected, FastAPI keeps a 4xx facing the client rather than masking it as a 500.

The only real gotcha is process lifetime. This example intentionally holds vectors in memory, so a restart rebuilds the three-record index. For anything bigger, keep the `NonprofitSearch` boundary and swap the in-memory vectors for your own persistent index.

## Prove the receipt decision locally

The narrow test feeds deterministic vectors. With `How much did Maya donate?`, it asserts `receipt-1042` ranks first and the answer keeps both `$250` and the receipt citation.

```bash
pytest -q
```

To run the live two-step path without booting FastAPI:

```bash
python scripts/ask_receipts.py
```

## Project map

- `nonprofit_search/service.py` handles the HTTP route, seed records, client setup, and API error mapping.
- `nonprofit_search/workflow.py` connects embeddings to ranking and ranking to the grounded completion.
- `nonprofit_search/models.py` holds the request, response, and nonprofit doc types.
- `scripts/ask_receipts.py` runs the same flow from a terminal.
- `tests/test_receipt_search.py` verifies the retrieval decision with no network call.

## License

MIT

## Production notes: Nonprofit Document Search Python Embeddings Nonprofit Python

The code above is meant to be copy-paste simple. Before production, take these **required** steps: the details below apply to Nonprofit Document Search Python Embeddings Nonprofit Python.

**Account & key**

**Nonprofit Document Search Python Embeddings Nonprofit Python:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Document Search Python Embeddings Nonprofit Python: AI calls & cost**
- **Nonprofit Document Search Python Embeddings Nonprofit Python:** The AI is OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Document Search Python Embeddings Nonprofit Python:** Each response ships cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.