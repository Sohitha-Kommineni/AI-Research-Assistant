# AI Research Assistant

A full-stack research assistant that lets you upload documents (PDF, TXT, or URL)
and ask questions that are answered only from those sources, with citations.
<p align="left">
  <img src="https://raw.githubusercontent.com/Sohitha-Kommineni/AI-Research-Assistant/a54d425fa93275c705af9941c8e02d6df862d085/images/Screenshot%202026-02-08%20011858.png" width="250" height="300" />
  <img src="https://raw.githubusercontent.com/Sohitha-Kommineni/AI-Research-Assistant/a54d425fa93275c705af9941c8e02d6df862d085/images/Screenshot%202026-02-07%20221942.png" width="250" height="300" />
  <img src="https://raw.githubusercontent.com/Sohitha-Kommineni/AI-Research-Assistant/a54d425fa93275c705af9941c8e02d6df862d085/images/Screenshot%202026-02-08%20010349.png" width="250" height="300" />
</p>

## Highlights
- Project-based workspaces with isolated sources and chat history
- PDF/TXT/URL ingestion with background processing
- RAG pipeline with citations and source snippets
- Streaming chat responses
- Clean, research-focused UI for desktop and tablet

## What it does
- Upload and manage research sources per project.
- Ask questions in a chat interface with cited sources.
- Keeps projects, documents, and chat history separate per user.
- Uses retrieval-augmented generation (RAG) to ground answers in documents.
- Returns "I don't know." when the answer is not present in the sources.

## Tech stack
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: React (Vite)
- RAG: chunking + embeddings + cosine retrieval + OpenAI LLM

## Local development (Docker)
1. Start services:
   - `docker compose up --build`
2. Frontend: `http://localhost:5173`
3. Backend: `http://localhost:8000`

## Quick start (UI)
1. Sign up → create a project.
2. Upload a PDF/TXT or add a URL.
3. Wait until the document status becomes **ready**.
4. Ask questions and review citations in the source panel.

## Environment variables
Backend:
- `DATABASE_URL` (default in compose file)
- `JWT_SECRET`
- `OPENAI_API_KEY` (enables real embeddings + LLM answers)

Frontend:
- `VITE_API_URL` (defaults to `http://localhost:8000`)

## Core API routes (backend)
Auth:
- `POST /auth/signup`
- `POST /auth/login`

Projects:
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`

Documents:
- `GET /projects/{project_id}/documents`
- `POST /projects/{project_id}/documents/upload`
- `POST /projects/{project_id}/documents/url`
- `GET /projects/{project_id}/documents/{document_id}/text`

Chat:
- `GET /projects/{project_id}/chat`
- `POST /projects/{project_id}/chat`
- `POST /projects/{project_id}/chat/stream`

## Example workflow
1. Upload a research PDF.
2. Ask: "What is the definition of research in this document?"
3. Receive a grounded answer with citations like `[1]`.
4. Click citations to inspect the source snippet.

## Usage notes
- If a PDF is scanned (no text layer), upload an OCR version for best results.

## Troubleshooting
- **"I don't know."**: Make sure the document status is **ready** and the
  question is clearly answered in the text. If not, re-upload the document.
- **View text empty**: The PDF likely has no text layer. Use OCR and re-upload.
- **OpenAI 429**: Your API quota is exhausted; add billing or remove the key.

## Deployment notes
- The project ships with Docker Compose for local development.
- For production, use a managed PostgreSQL instance and set environment
  variables via your hosting provider.

## Security considerations (baseline)
- Replace `JWT_SECRET` in production.
- Do not commit `.env` files or API keys.
