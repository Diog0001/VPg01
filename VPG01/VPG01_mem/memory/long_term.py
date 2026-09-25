from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

import chromadb
from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

from config import CHROMA_DIR, RAG_TOP_K


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    distance: float | None = None


class LongTermMemory:
    """Долгая память: векторная база ChromaDB, отдельная коллекция на пользователя."""

    def __init__(self, persist_dir: Path | None = None) -> None:
        path = persist_dir or CHROMA_DIR
        path.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._client = chromadb.PersistentClient(path=str(path))
        self._embedder = ONNXMiniLM_L6_V2()

    def add_chunks(self, user_id: int, filename: str, chunks: list[str]) -> int:
        if not chunks:
            return 0

        collection = self._collection(user_id)
        ids = [str(uuid4()) for _ in chunks]
        metadatas = [
            {
                "source": filename,
                "chunk_index": index,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
            for index, _ in enumerate(chunks)
        ]
        collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        return len(chunks)

    def replace_chunks(self, user_id: int, filename: str, chunks: list[str]) -> int:
        collection = self._collection(user_id)
        try:
            collection.delete(where={"source": filename})
        except Exception:
            pass
        return self.add_chunks(user_id, filename, chunks)

    def query(self, user_id: int, question: str, top_k: int = RAG_TOP_K) -> list[RetrievedChunk]:
        collection = self._collection(user_id)
        if collection.count() == 0:
            return []

        result = collection.query(
            query_texts=[question],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        chunks: list[RetrievedChunk] = []
        for text, meta, distance in zip(documents, metadatas, distances):
            if not text:
                continue
            chunks.append(
                RetrievedChunk(
                    text=text,
                    source=str((meta or {}).get("source") or "документ"),
                    distance=float(distance) if distance is not None else None,
                )
            )
        return chunks

    def list_sources(self, user_id: int) -> list[str]:
        collection = self._collection(user_id)
        if collection.count() == 0:
            return []
        data = collection.get(include=["metadatas"])
        names = []
        for meta in data.get("metadatas") or []:
            source = str((meta or {}).get("source") or "")
            if source and source not in names:
                names.append(source)
        return names

    def chunk_count(self, user_id: int) -> int:
        return self._collection(user_id).count()

    def clear(self, user_id: int) -> None:
        name = self._collection_name(user_id)
        with self._lock:
            try:
                self._client.delete_collection(name)
            except Exception:
                pass

    def _collection(self, user_id: int):
        name = self._collection_name(user_id)
        with self._lock:
            return self._client.get_or_create_collection(
                name=name,
                embedding_function=self._embedder,
                metadata={"hnsw:space": "cosine"},
            )

    @staticmethod
    def _collection_name(user_id: int) -> str:
        return f"user_{abs(user_id)}"
