import Fastify from "fastify";

const app = Fastify({ logger: true });

const PYTHON_SERVICE_URL = "http://127.0.0.1:8001/process";

// endpoint: POST /upload-transactions
// Accepts a JSON array of mixed raw transactions from both source systems, forwards them to the Python processing layer for normalization & categorization, and returns the processed result
app.post("/upload-transactions", async (request, reply) => {
  const transactions = request.body;

  if (!Array.isArray(transactions)) {
    return reply.status(400).send({
      error: "Request body must be a JSON array of transactions",
    });
  }

  // Forward to the Python processing layer
  const response = await fetch(PYTHON_SERVICE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(transactions),
  });

  if (!response.ok) {
    const errorText = await response.text();
    return reply.status(502).send({
      error: "Python processing service returned an error",
      details: errorText,
    });
  }

  const result = await response.json();
  return reply.send(result);
});

const start = async () => {
  try {
    await app.listen({ port: 3000, host: "0.0.0.0" });
    console.log("Fastify API running on http://localhost:3000");
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
};

start();
