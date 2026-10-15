"""Persistent Chroma storage with explicit embedding model isolation."""
import hashlib
import logging
import re
from collections import Counter
from pathlib import Path
import chromadb

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, path: Path | str, embedding_model: str):
        self.embedding_model = embedding_model
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            "knowledge", metadata={"hnsw:space": "cosine", "embedding_model": embedding_model})
        current = (self.collection.metadata or {}).get("embedding_model")
        if current and current != embedding_model:
            raise ValueError(f"Index uses embedding model '{current}', configured model is '{embedding_model}'. Clear the index before changing models.")
        if not current:
            self.collection.modify(metadata={"hnsw:space": "cosine", "embedding_model": embedding_model})

    @staticmethod
    def chunk_id(document_id: str, chunk_number: int) -> str:
        return hashlib.sha256(f"{document_id}:{chunk_number}".encode()).hexdigest()

    def has_document(self, document_id: str) -> bool:
        return bool(self.collection.get(where={"document_id": document_id}, include=[])["ids"])

    def upsert_document(self, document_id: str, filename: str, content_hash: str,
                        chunks, embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings) or not chunks:
            raise ValueError("Chunks and embeddings must be non-empty and have equal lengths.")
        ids = [self.chunk_id(document_id, c.chunk_number) for c in chunks]
        metadatas = [{"document_id": document_id, "filename": filename,
            "content_hash": content_hash, "chunk_number": c.chunk_number,
            "page": c.page or 0} for c in chunks]
        # Add new records first. Stable ids then update atomically per chunk; old tails are removed last.
        old_ids = self.collection.get(where={"document_id": document_id}, include=[])["ids"]
        same_name = self.collection.get(where={"filename": filename}, include=["metadatas"])
        replaced_document_ids = {m["document_id"] for m in same_name["metadatas"]
                                 if m["document_id"] != document_id}
        self.collection.upsert(ids=ids, documents=[c.text for c in chunks],
            embeddings=embeddings, metadatas=metadatas)
        obsolete = list(set(old_ids) - set(ids))
        if obsolete:
            self.collection.delete(ids=obsolete)
        # Only remove a previous same-name version after the replacement upsert succeeds.
        for replaced_id in replaced_document_ids:
            self.delete_document(replaced_id)

    def search(self, embedding: list[float], top_k: int = 5,
               threshold: float | None = None, query_text: str = "") -> list[dict]:
        if self.collection.count() == 0:
            return []
        count = self.collection.count()
        candidate_count = min(max(top_k * 4, top_k), count)
        result = self.collection.query(query_embeddings=[embedding], n_results=candidate_count,
                                       include=["documents", "metadatas", "distances"])
        semantic = []
        for rank, (text, metadata, distance) in enumerate(zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0]), 1):
            # ChromaDB cosine space: distance = 1.0 - cosine_similarity.
            # Convert distance to normalized cosine similarity score bounded in [-1.0, 1.0].
            similarity = max(-1.0, min(1.0, 1.0 - distance))
            # Only filter if a positive threshold is explicitly provided
            if threshold is None or threshold <= 0.0 or similarity >= threshold:
                semantic.append((text, metadata, similarity, rank))

        # Lexical retrieval complements embeddings for exact terms such as names,
        # dates, identifiers, and quoted phrases. Fuse ranks to avoid incompatible
        # raw-score scales between cosine similarity and keyword matching.
        query = self.collection.get(include=["documents", "metadatas"])
        terms = [t.casefold() for t in re.findall(r"[\w.-]+", query_text) if len(t) > 1]
        lexical = []
        qcounts = Counter(terms) if terms else Counter()
        if terms:
            for text, metadata in zip(query["documents"], query["metadatas"]):
                words = Counter(t.casefold() for t in re.findall(r"[\w.-]+", text))
                score = sum(min(n, words[t]) for t, n in qcounts.items())
                if score:
                    lexical.append((text, metadata, score))
            lexical.sort(key=lambda item: item[2], reverse=True)
            lexical = lexical[:candidate_count]

        fused: dict[str, dict] = {}
        for text, metadata, sim_score, rank in semantic:
            key = self.chunk_id(metadata["document_id"], metadata["chunk_number"])
            fused[key] = {
                "text": text,
                "metadata": metadata,
                "score": max(0.0, sim_score),
                "_rank_score": 1 / (60 + rank)
            }
        for rank, (text, metadata, lexical_score) in enumerate(lexical, 1):
            key = self.chunk_id(metadata["document_id"], metadata["chunk_number"])
            lex_norm = (lexical_score / sum(qcounts.values())) if qcounts else 0.0
            if key in fused:
                fused[key]["_rank_score"] += 1 / (60 + rank)
            else:
                fused[key] = {
                    "text": text,
                    "metadata": metadata,
                    "score": max(0.0, min(1.0, lex_norm)),
                    "_rank_score": 1 / (60 + rank)
                }

        found = sorted(fused.values(), key=lambda item: item["_rank_score"], reverse=True)[:top_k]
        for item in found:
            item.pop("_rank_score", None)

        logger.info("VectorStore search complete: total_in_db=%d, semantic_found=%d, lexical_found=%d, fused_returned=%d",
                    count, len(semantic), len(lexical), len(found))
        return found

    def documents(self) -> list[dict]:
        records = self.collection.get(include=["metadatas"])
        counts: dict[str, dict] = {}
        for metadata in records["metadatas"]:
            key = metadata["document_id"]
            entry = counts.setdefault(key, {"document_id": key, "filename": metadata["filename"], "chunks": 0})
            entry["chunks"] += 1
        return list(counts.values())

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def clear(self) -> None:
        self.client.delete_collection("knowledge")
        self.collection = self.client.get_or_create_collection(
            "knowledge", metadata={"hnsw:space": "cosine", "embedding_model": self.embedding_model})
