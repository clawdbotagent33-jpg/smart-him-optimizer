"""문서 관리 API 엔드포인트 - 다양한 파일 포맷 지원"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
import os
from datetime import datetime
import uuid

from api.schemas import DocumentUploadResponse, RAGQueryRequest, RAGQueryResponse
from rag.embedding import embedding_service, text_chunker
from rag.retriever import rag_retriever
from core.config import settings
from services.document_processor import DocumentProcessor

router = APIRouter()

# 메모리 문서 저장소
MEMORY_DOCUMENTS = {}


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Form(None),
):
    """문서 업로드 및 RAG 학습 - 다양한 파일 포맷 지원"""
    # 파일 확장자 확인
    file_ext = os.path.splitext(file.filename)[1].lower()
    supported_extensions = DocumentProcessor.get_supported_extensions()

    if file_ext not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다: {file_ext}\n"
                    f"지원 형식: 텍스트({', '.join(sorted(DocumentProcessor.SUPPORTED_TEXT_FORMATS))}), "
                    f"PDF({', '.join(sorted(DocumentProcessor.SUPPORTED_PDF_FORMATS))}), "
                    f"Word({', '.join(sorted(DocumentProcessor.SUPPORTED_WORD_FORMATS))}), "
                    f"Excel({', '.join(sorted(DocumentProcessor.SUPPORTED_EXCEL_FORMATS))})"
        )

    # 파일 저장
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, temp_filename)

    try:
        # 파일 읽기
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 문서 처리 서비스로 텍스트 추출
        processor = DocumentProcessor()
        process_result = processor.process_document(file_path, file.filename)

        # 처리 오류 확인
        if process_result.get('error'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=process_result['error']
            )

        text_content = process_result['text']

        # 텍스트가 비어있는지 확인
        if not text_content or len(text_content.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="추출된 텍스트가 없거나 너무 짧습니다."
            )

        # 메타데이터 구성
        metadata = process_result['metadata'].copy()
        metadata.update({
            'doc_type': doc_type or 'manual',
            'uploaded_by': 'test_user',
            'uploaded_at': datetime.utcnow().isoformat(),
            'file_size': len(content),
            'page_count': process_result.get('page_count', 1)
        })

        # 문서 유형 분류 (기본값)
        if not doc_type:
            # 파일 확장자로 자동 분류
            if file_ext == '.pdf':
                doc_type = 'guideline'
            elif file_ext in DocumentProcessor.SUPPORTED_WORD_FORMATS:
                doc_type = 'manual_memo'
            elif file_ext in DocumentProcessor.SUPPORTED_EXCEL_FORMATS:
                doc_type = 'performance_metric'
            else:
                doc_type = 'manual'
            metadata['doc_type'] = doc_type

        # 청킹
        chunks = text_chunker.chunk_document(
            content=text_content,
            metadata=metadata
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="문서를 청킹할 수 없습니다."
            )

        # 메모리에 문서 저장
        doc_id = str(uuid.uuid4())
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"doc_{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk['text'])
            chunk_metadata = chunk['metadata'].copy()
            chunk_metadata['document_id'] = doc_id
            chunk_metadatas.append(chunk_metadata)

        # 임베딩 및 저장
        success = embedding_service.add_documents(
            documents=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="임베딩 저장 중 오류가 발생했습니다."
            )

        MEMORY_DOCUMENTS[doc_id] = {
            "id": doc_id,
            "doc_type": doc_type,
            "title": file.filename,
            "content": text_content,
            "chunks": len(chunks),
            "uploaded_by": "test_user",
            "metadata": metadata
        }

        # 임시 파일 삭제
        try:
            os.remove(file_path)
        except:
            pass

        return DocumentUploadResponse(
            document_id=doc_id,
            title=file.filename,
            doc_type=doc_type,
            chunks_created=len(chunks)
        )

    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        # 일반 오류
        # 임시 파일 정리
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 처리 중 오류 발생: {str(e)}"
        )


@router.post("/documents/query", response_model=RAGQueryResponse)
async def query_documents(
    request: RAGQueryRequest,
):
    """RAG 기반 문서 질의"""
    try:
        result = await rag_retriever.query_with_rag(
            question=request.question,
            context_type=request.context_type,
            use_llm=request.use_llm
        )

        return RAGQueryResponse(
            question=request.question,
            answer=result.get('answer'),
            sources=result.get('sources', [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질의 처리 중 오류 발생: {str(e)}"
        )


@router.get("/documents/stats")
async def get_document_stats():
    """문서 통계 조회"""
    stats = embedding_service.get_collection_stats()

    # 메모리 문서 정보 추가
    stats['document_count'] = len(MEMORY_DOCUMENTS)
    stats['status'] = 'active'

    return stats


@router.get("/documents")
async def list_documents():
    """업로드된 문서 목록 조회"""
    documents = []
    for doc_id, doc_info in MEMORY_DOCUMENTS.items():
        documents.append({
            "id": doc_id,
            "title": doc_info["title"],
            "doc_type": doc_info["doc_type"],
            "chunks": doc_info["chunks"],
            "uploaded_by": doc_info["uploaded_by"],
            "metadata": doc_info.get("metadata", {})
        })
    return {"documents": documents}


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
):
    """문서 삭제"""
    if document_id not in MEMORY_DOCUMENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )

    # 청크 ID 찾기
    chunk_count = MEMORY_DOCUMENTS[document_id].get('chunks', 0)
    chunk_ids = [f"doc_{document_id}_chunk_{i}" for i in range(chunk_count)]
    embedding_service.delete_documents(chunk_ids)

    # 메모리에서 삭제
    del MEMORY_DOCUMENTS[document_id]

    return {"message": "문서가 삭제되었습니다"}
