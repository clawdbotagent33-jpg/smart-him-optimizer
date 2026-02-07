"""RAG 임베딩 모듈 - ChromaDB 없는 버전"""
import os
from typing import List, Dict, Any, Optional
import numpy as np

from core.config import settings


class EmbeddingService:
    """문서 임베딩 서비스 - 메모리 버전 (ChromaDB 없이)"""

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.model = None
        # 메모리 저장소
        self.documents = {}
        self.embeddings = {}

    def load_model(self):
        """임베딩 모델 로드 (선택적)"""
        if self.model is None:
            # ChromaDB가 없으므로 임시로 간단한 임베딩 사용
            return None
        return self.model

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """텍스트 임베딩 생성 - 간단 버전"""
        # 간단한 TF-IDF 스타일 벡터 생성 (실제로는 sentence-transformers 사용 권장)
        import re
        from collections import Counter

        embeddings = []
        for text in texts:
            # 간단한 단어 빈도 기반 임베딩
            words = re.findall(r'\w+', text.lower())
            counter = Counter(words)
            # 고정 크기 벡터 (간단 구현)
            vec = np.zeros(100)
            for i, word in enumerate(list(set(words))[:100]):
                vec[i] = counter.get(word, 0) / len(words)
            embeddings.append(vec)

        return np.array(embeddings)

    def init_chroma(self, collection_name: str = "smart_him_docs"):
        """ChromaDB 클라이언트 초기화 - 메모리 버전"""
        # 메모리에 저장
        return self

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str],
        collection_name: str = "smart_him_docs"
    ) -> bool:
        """문서 추가 (메모리)"""
        try:
            embeddings = self.get_embeddings(documents)

            for doc_id, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
                self.documents[doc_id] = {
                    "text": doc,
                    "metadata": meta,
                    "embedding": emb.tolist()
                }
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[dict] = None,
        collection_name: str = "smart_him_docs"
    ) -> dict:
        """유사 문서 검색 (코사인 유사도)"""
        try:
            query_embedding = self.get_embeddings([query])[0]

            # 코사인 유사도 계산
            results = []
            for doc_id, doc_data in self.documents.items():
                if filter_dict and doc_data["metadata"].get(list(filter_dict.keys())[0]) != list(filter_dict.values())[0]:
                    continue

                doc_emb = np.array(doc_data["embedding"])
                # 코사인 유사도
                similarity = np.dot(query_embedding, doc_emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb))

                results.append({
                    "id": doc_id,
                    "text": doc_data["text"],
                    "metadata": doc_data["metadata"],
                    "similarity": float(similarity)
                })

            # 유사도 순 정렬
            results.sort(key=lambda x: x["similarity"], reverse=True)

            return {
                "documents": [[r["text"] for r in results[:n_results]]],
                "metadatas": [[r["metadata"] for r in results[:n_results]]],
                "distances": [[1 - r["similarity"] for r in results[:n_results]]]
            }
        except Exception as e:
            print(f"Error searching documents: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    def delete_documents(
        self,
        ids: List[str],
        collection_name: str = "smart_him_docs"
    ) -> bool:
        """문서 삭제 (메모리)"""
        for doc_id in ids:
            self.documents.pop(doc_id, None)
        return True

    def get_collection_stats(self, collection_name: str = "smart_him_docs") -> dict:
        """컬렉션 통계 정보"""
        return {
            "collection_name": collection_name,
            "document_count": len(self.documents),
            "status": "active"
        }


class TextChunker:
    """텍스트 청킹 처리 클래스"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk_text(self, text: str) -> List[dict]:
        """텍스트를 청크로 분할"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # 문장 경계를 찾아 청크 분할
            if end < text_length:
                for sep in self.separators:
                    sep_pos = text.rfind(sep, start, end)
                    if sep_pos != -1:
                        end = sep_pos + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append({
                    "text": chunk,
                    "start": start,
                    "end": end
                })

            start = end - self.chunk_overlap

        return chunks

    def chunk_document(
        self,
        content: str,
        metadata: dict
    ) -> List[dict]:
        """문서 청킹 (메타데이터 포함)"""
        text_chunks = self.chunk_text(content)
        result = []

        for i, chunk in enumerate(text_chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_start": chunk["start"],
                "chunk_end": chunk["end"]
            })
            result.append({
                "text": chunk["text"],
                "metadata": chunk_metadata
            })

        return result


# 전역 인스턴스
embedding_service = EmbeddingService()
text_chunker = TextChunker(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)
