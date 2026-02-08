from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ChatMessage, Document, DocumentChunk, Project
from app.schemas import Citation
from app.services.embeddings import embed_texts
from app.services.vector_store import cosine_similarity, top_k


MIN_SIMILARITY = 0.18
TOP_K = 8


def _format_prompt(question: str, chunks: List[Tuple[int, str]]) -> str:
    sources = "\n\n".join([f"[{idx + 1}] {content}" for idx, content in chunks])
    return (
        "You are an AI research assistant. Answer only using the sources. "
        "If the answer is not in the sources, say \"I don't know.\" "
        "Cite sources with bracket numbers like [1].\n\n"
        f"Question: {question}\n\nSources:\n{sources}\n\nAnswer:"
    )


def _llm_answer(prompt: str) -> str:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def _fallback_answer(question: str, chunks: List[Tuple[int, str]]) -> str:
    if not chunks:
        return "I don't know."
    top_snippet = chunks[0][1]
    return f"{top_snippet} [1]"


def answer_question(
    db: Session, project: Project, user_id: int, question: str
) -> tuple[str, List[Citation], List[dict]]:
    chunk_rows = (
        db.query(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(DocumentChunk.project_id == project.id)
        .all()
    )

    if not chunk_rows:
        answer = "I don't know."
        citations: List[Citation] = []
        used_chunks: List[dict] = []
        return answer, citations, used_chunks

    valid_rows = [row for row in chunk_rows if row[0].embedding]
    if not valid_rows:
        answer = "I don't know."
        citations = []
        used_chunks = []
        return answer, citations, used_chunks

    embeddings = [row[0].embedding for row in valid_rows]
    query_embedding = embed_texts([question])[0]
    similarities = cosine_similarity(query_embedding, embeddings)
    selected_indices = top_k(similarities, TOP_K)

    selected = []
    for idx in selected_indices:
        chunk, document = valid_rows[idx]
        score = similarities[idx]
        selected.append((chunk, document, score))

    min_similarity = 0.0 if not settings.openai_api_key else MIN_SIMILARITY
    selected = [item for item in selected if item[2] >= min_similarity]
    if not selected:
        answer = "I don't know."
        citations = []
        used_chunks = []
        return answer, citations, used_chunks

    prompt_chunks = [(idx, item[0].content) for idx, item in enumerate(selected)]
    prompt = _format_prompt(question, prompt_chunks)

    if settings.openai_api_key:
        answer = _llm_answer(prompt)
    else:
        answer = _fallback_answer(question, prompt_chunks)

    citations = []
    used_chunks = []
    for idx, (chunk, document, score) in enumerate(selected, start=1):
        citations.append(
            Citation(
                document_id=document.id,
                document_name=document.name,
                page_number=chunk.page_number,
                snippet=chunk.content[:400],
            )
        )
        used_chunks.append(
            {
                "document_id": document.id,
                "document_name": document.name,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "score": score,
            }
        )

    db.add(
        ChatMessage(
            project_id=project.id,
            user_id=user_id,
            role="user",
            content=question,
            sources_json=None,
        )
    )
    db.add(
        ChatMessage(
            project_id=project.id,
            user_id=user_id,
            role="assistant",
            content=answer,
            sources_json=[c.dict() for c in citations],
        )
    )
    project.last_activity_at = datetime.utcnow()
    db.commit()

    return answer, citations, used_chunks
