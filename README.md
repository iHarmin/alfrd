# ALFRD Technical Task: Mini-ETL Pipeline

A mini ETL pipeline that ingests raw financial transactions from multiple ERP systems (QuickBooks, Xero), then normalizes them into a schema, and flags transactions where the AI categorizer produces bad output.

## Project Structure

```
alfrd/
├── api/                        # TypeScript + Fastify API layer
│   └── src/server.ts           # POST /upload-transactions endpoint
├── processing/                 # Python processing layer
│   ├── app.py                  # FastAPI service (POST /process)
│   ├── schemas.py              # Pydantic NormalizedTransaction schema
│   ├── normalizer.py           # Maps QuickBooks/Xero
│   └── categorizer.py          # Calls LLM + catches bad outputs
├── dummy_llm.py                # Already given
├── sample_payload.json         # Already given
├── PLANNING.md                 # Architecture & design decisions
└── README.md                   
```

## Setup

### Clone the repo

```bash
git clone https://github.com/iHarmin/alfrd.git
cd alfrd-task
```

### Python (processing layer)

```bash
pip3 install fastapi uvicorn pydantic
```
OR
```bash
pip install -r processing/requirements.txt
```
### Node (API layer)

```bash
cd api
npm install
```

## Running

**Terminal 1 — Start the Python processing service:**

```bash
python3 -m uvicorn processing.app:app --port 8001
```

**Terminal 2 — Start the Fastify API:**

```bash
cd api
./node_modules/.bin/tsx src/server.ts
```

## Testing

Send the sample payload to the Fastify endpoint:

```bash
curl -s -X POST http://localhost:3000/upload-transactions \
  -H "Content-Type: application/json" \
  -d @sample_payload.json | python3 -m json.tool
```

To save output to a file:

```bash
curl -s -X POST http://localhost:3000/upload-transactions \
  -H "Content-Type: application/json" \
  -d @sample_payload.json > output.json
```

## How the pipeline works 

1. Fastify receives raw transactions at `POST /upload-transactions`
2. Forwards them to the Python service at `POST /process`
3. Python normalizes each transaction (different field names, date formats, garbage values)
4. Runs the dummy LLM categorizer on each one
5. Catches null returns, hallucinated categories, bad amounts, empty descriptions
6. Flags bad transactions for human review with clear reasons
7. Returns a JSON response with summary counts and the full normalized list
