from __future__ import annotations

from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.services.embeddings import embed_texts


CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def _chunk_text(text: str) -> List[str]:
    text = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
        if start < 0:
            start = 0
        if end == len(text):
            break
    return [chunk for chunk in chunks if chunk.strip()]


def parse_pdf(path: str) -> Tuple[str, List[Tuple[int, str]]]:
    reader = PdfReader(path)
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        content = page.extract_text() or ""
        pages.append((idx, content))
    full_text = "\n".join(page[1] for page in pages)
    return full_text, pages


def parse_text(text: str) -> Tuple[str, List[Tuple[int, str]]]:
    return text, [(1, text)]


def parse_url(url: str) -> Tuple[str, List[Tuple[int, str]]]:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return text, [(1, text)]


def build_chunks(pages: List[Tuple[int, str]]) -> List[dict]:
    chunk_payloads = []
    for page_number, page_text in pages:
        for chunk in _chunk_text(page_text):
            chunk_payloads.append(
                {
                    "content": chunk,
                    "page_number": page_number,
                }
            )
    return chunk_payloads


def embed_chunks(chunks: List[dict]) -> List[dict]:
    texts = [chunk["content"] for chunk in chunks]
    embeddings = embed_texts(texts)
    for chunk, vector in zip(chunks, embeddings):
        chunk["embedding"] = vector
    return chunks
