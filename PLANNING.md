# Planning

## How I structured the system and why

### Two separate services

I built this as two services that talk to each other over HTTP:

1. **A TypeScript API** (Fastify) running on port 3000. It receives the raw transactions at `POST /upload-transactions`.
2. **A Python processing service** (FastAPI) running on port 8001. This is the stage where data is cleaned, the LLM is called, and problems are flagged.

I kept them separate for a simple reason: each one does one job. The TypeScript side deals with HTTP stuff (accepting requests, validating input, returning responses). The Python side deals with the business logic (parsing messy data, running the categorizer, handling errors).

### How the two services communicate

The flow:

1. A client sends a POST request to the Fastify server with an array of raw transactions.
2. Fastify checks that the body is actually an array. If not, it sends back a 400 error right away.
3. If it's valid, Fastify forwards the whole array to the Python service at `POST /process`.
4. Python does all the normalization and categorization work.
5. Python sends back the result. Fastify passes it straight through to the client.

I went with HTTP between the two services instead of something like spawning a subprocess. HTTP is simpler to debug and test. I can hit either service with curl independently, which made development much easier. And if we ever need to scale the Python service separately from the API, they are already independent.

### How I designed the schema

I needed one unified schema for transactions, no matter which ERP system they came from. I built a Pydantic model called `NormalizedTransaction` with these fields:

- **id** — I kept the original reference from the source system (like "QB-99381A" or "X-10029"). This way you can always trace back to the source.
- **date** — I convert everything to ISO format (YYYY-MM-DD). QuickBooks already uses this. Xero uses DD/MM/YYYY, so I parse and convert it.
- **description** — the `memo` from QuickBooks or `description` from Xero. If it's empty, I flag the transaction for review.
- **amount** — I try to turn it into a number. If the source sent something like "TBD" or "PENDING" or null, I set amount to null and flag it.
- **currency** — defaults to GBP. I confirmed this with the founder Sammi Teki since neither QuickBooks nor Xero includes a currency field in the sample data.
- **category** — whatever the LLM returns, or null if it returned something bad.
- **needs_review** — true if the transaction has any issue that needs a human review, false otherwise.
- **review_reasons** — a list of strings explaining what's wrong. I made this a list (not a single string) because one transaction can have multiple issues. For example, QB-99390J has both a bad amount ("PENDING") and a failed LLM call. Both reasons show up.

---

## How I handle bad LLM outputs

### What the LLM does

The dummy_llm.py simulates a categorization model. It takes a transaction description and returns a category. But it's unreliable on purpose:

- About 65% of the time, it gives back a valid category (SOFTWARE, MEALS, TRAVEL, UTILITIES, or PAYROLL).
- About 15% of the time, it returns null — like a real API timing out or failing.
- About 20% of the time, it makes up a category that doesn't exist, like "Super Secret Expense", "Miscellaneous Operations Cost" or "Unknown Financial Activity." This is what hallucination looks like.

### What I do about it

After every LLM call, I check the result against the list of valid categories. There are only three things that can happen:

1. **The LLM gave me a valid category** — I use it. Done. No flag needed.
2. **The LLM gave me null** — I set the category to null, mark the transaction for review, and record the reason: "LLM returned null — possible timeout or failure."
3. **The LLM gave me a string that's not in the valid list** — I set the category to null, mark the transaction for review, and record the reason: "LLM returned invalid category: 'Super Secret Expense'" (or whatever it made up).

**Important Note:** One thing I want to call out is that when the LLM returns a valid category that's technically "wrong" (like saying "TRAVEL" for a salary payment), I still accept it. That's a model quality issue, not a pipeline issue. I think the pipeline's job is to catch structurally bad outputs — null, hallucinated strings, things that aren't in the valid set. **Improving the model's accuracy is a separate problem as I cannot modify dummy_llm.py**. I think this distinction matters because in production, you'd fix accuracy by fine-tuning the model or improving prompts, not by adding guesswork to the data pipeline.

### What I had do differently in production

- **Retry before flagging:** If the LLM returns null, I had retry once or twice with a short backoff before giving up. Timeouts are often temporary.
- **Confidence scores:** A LLM can tell you how confident it is. I had flag low-confidence results even if the category is technically valid.
- **A keyword-based fallback:** If the LLM fails, I had try a simple rules engine as a backup. For example, if the description contains "Airlines" or "flight," guess TRAVEL. Only flag for human review if both the LLM and the fallback can't figure it out. This would cut down the number of transactions that need manual review.

---

## How I had handle this at scale

### The problem

Right now, I process everything in one synchronous HTTP request. That works for 28 transactions. But if input files were 50MB each (tens of thousands of transactions), this approach would break. The request would time out. Memory usage would spike. The LLM calls alone would take a lot of time in my opinion.

Here's how I had change things:

### 1. Don't load everything into memory at once

Instead of accepting a JSON array in the request body, I had let the client upload a file. Then I had parse it in chunks using something like `ijson` in Python, which reads JSON incrementally without loading the whole thing. 

### 2. Making it asynchronous

Instead of making the client wait for the whole batch to finish, I'd return a job ID immediately. The actual processing would happen in the background using a job queue like Redis, RabbitMQ, or SQS. The flow would look like:

```
Client sends POST /upload-transactions and gets back { jobId: "abc123" }
Background service pick up the job and process batches
Client checks GET /jobs/abc123 to see progress 
```

This way the client never have to really wait in my opinion. And if the server restarts, the job queue keeps track of where things left off.

### 3. Run LLM calls in parallel

The dummy LLM has 50-200ms of latency per call. With 50,000 transactions in a row, that's roughly 40 minutes just waiting for the LLM. I had use Python's `asyncio` to run many LLM calls at once — maybe 50 or 100 in parallel. This would bring the total time down.

### 4. Isolating failures

If a batch fails (for example, due to a crash on unexpected input), the entire job shouldn’t stop. Each batch is processed independently. Failed batches are sent to a retry queue, and after several unsuccessful attempts, they move to a queue for manual review while the rest of the job continues running.

### 5. Streaming the output

Instead of building a huge JSON response in memory, I had write results to a file or database as each batch finishes. I guess in my opinion NDJSON (one JSON object per line) is a good format for this — it's easy to append to and easy to process later without loading it all at once.

### Idea (based on my experience)

According to experience with previous multiple projects, I think at scale, the pattern shifts from "send request, wait for response" to "submit a job, process in the background, notify when done." The API layer remains thin, while heavy processing is handled by background service that can scale as needed. The focus is on ensuring no data is lost, the client isn’t blocked, and failures in one part don’t affect the rest of the system.