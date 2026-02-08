import OpenAI from "openai";

const client = new OpenAI();

const response = await client.responses.create({
  model: "gpt-4.1-mini",
  input: "Say hello from my AI research assistant."
});

console.log(response.output_text);

const emb = await client.embeddings.create({
  model: "text-embedding-3-large",
  input: "Hello world"
});

console.log("Embedding length:", emb.data[0].embedding.length);
