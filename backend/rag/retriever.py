"""RAG 검색 및 생성 모듈"""
import json
from typing import List, Dict, Any, Optional
import httpx

from core.config import settings
from rag.embedding import embedding_service


class RAGRetriever:
    """RAG 검색 및 응답 생성"""

    def __init__(self):
        self.embedding_service = embedding_service
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.llm_model = settings.LLM_MODEL

    async def search_relevant_guidelines(
        self,
        query: str,
        doc_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """관련 가이드라인 검색"""
        filter_dict = {"doc_type": doc_type} if doc_type else None
        results = self.embedding_service.search(
            query=query,
            n_results=n_results,
            filter_dict=filter_dict
        )

        documents = []
        if results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0
                })

        return documents

    async def query_with_rag(
        self,
        question: str,
        context_type: str = "general",
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """RAG 기반 질의응답"""
        # 관련 문서 검색
        relevant_docs = await self.search_relevant_guidelines(
            query=question,
            doc_type=context_type,
            n_results=settings.TOP_K_RESULTS
        )

        # 컨텍스트 구성
        context = self._build_context(relevant_docs)

        response = {
            "question": question,
            "context": context,
            "sources": [doc["metadata"] for doc in relevant_docs],
            "answer": None
        }

        # LLM 생성 (옵션)
        if use_llm:
            response["answer"] = await self._generate_answer(question, context)

        return response

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """검색된 문서로 컨텍스트 구성"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "Unknown")
            context_parts.append(f"[출처 {i}: {source}]\n{doc['content']}")

        return "\n\n".join(context_parts)

    async def _generate_answer(self, question: str, context: str) -> str:
        """LLM으로 답변 생성"""
        try:
            # LLM이 없을 경우 간단한 규칙 기반 답변
            return f"[검색된 문맥 기반 답변]\n\n질문: {question}\n\n관련 문헌이 검색되었습니다. 상세 분석을 위해서는 의료진과 상의하시기 바랍니다."

        except Exception as e:
            return f"오류 발생: {str(e)}"

    def _build_prompt(self, question: str, context: str) -> str:
        """LLM 프롬프트 구성"""
        return f"""당신은 보건의료정보관리 전문가입니다. K-DRG v4.7 및 KCD-9 코딩 규정에 정통해 있습니다.

다음 문맥을 참고하여 질문에 답변해 주세요:

[참고 문맥]
{context}

[질문]
{question}

답변 시 주의사항:
1. K-DRG v4.7 규정을 기준으로 답변하세요.
2. 규정 근거를 명확히 제시하세요.
3. A그룹(전문질병군) 전환을 위한 요구사항이 있다면 구체적으로 설명하세요.
4. 불확실한 경우 "추가 검토 필요"라고 명시하세요.

답변:"""

    async def suggest_a_group_upgrade(
        self,
        principal_diagnosis: str,
        secondary_diagnoses: List[str],
        procedures: List[str],
        current_group: str
    ) -> Dict[str, Any]:
        """A그룹 전환 가능성 및 제안사항 분석"""
        query = f"""
        주진단: {principal_diagnosis}
        부진단: {', '.join(secondary_diagnoses)}
        처치: {', '.join(procedures)}
        현재 그룹: {current_group}

        A그룹(전문질병군)으로 격상하기 위해 필요한 추가 문서화나 코딩 제안
        """

        result = await self.query_with_rag(
            question=query,
            context_type="k_drg_guideline",
            use_llm=True
        )

        return {
            "current_group": current_group,
            "upgrade_suggestions": result.get("answer", ""),
            "required_documentation": self._extract_requirements(result.get("answer", "")),
            "sources": result.get("sources", [])
        }

    def _extract_requirements(self, answer: str) -> List[str]:
        """답변에서 필수 요구사항 추출"""
        requirements = []

        # 키워드 기반 추출 (간단 구현)
        keywords = ["합병증", "동반질환", "중증도", "처치", "시술"]
        for keyword in keywords:
            if keyword in answer:
                sentences = answer.split(". ")
                for sentence in sentences:
                    if keyword in sentence:
                        requirements.append(sentence.strip())

        return requirements

    async def generate_cdi_query(
        self,
        admission_id: str,
        missing_items: List[str],
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """CDI 쿼리 문구 생성"""
        query_text = f"""
        환자 ID: {admission_id}
        누락된 문서화 항목: {', '.join(missing_items)}

        의료진에게 보낼 정중한 문의 문구를 생성해 주세요.
        K-DRG v4.7 기준으로 적절한 코딩을 위해 필요한 사항임을 강조하세요.
        긴급도: {urgency}
        """

        result = await self.query_with_rag(
            question=query_text,
            context_type="cdi_template",
            use_llm=True
        )

        return {
            "admission_id": admission_id,
            "query_text": result.get("answer", ""),
            "missing_items": missing_items,
            "urgency": urgency
        }

    async def check_compliance(
        self,
        diagnosis_codes: List[str],
        documentation: str
    ) -> Dict[str, Any]:
        """KCD-9 규정 준수 검증"""
        query = f"""
        진단코드: {', '.join(diagnosis_codes)}
        문서화 내용: {documentation[:500]}

        이 코딩이 KCD-9 규정을 준수하는지 검증하고,
        문제가 있다면 올바른 코드를 제안해 주세요.
        """

        result = await self.query_with_rag(
            question=query,
            context_type="kcd9_guideline",
            use_llm=True
        )

        return {
            "is_compliant": "위반" not in result.get("answer", ""),
            "compliance_report": result.get("answer", ""),
            "suggested_codes": self._extract_suggested_codes(result.get("answer", ""))
        }

    def _extract_suggested_codes(self, text: str) -> List[str]:
        """제안된 코드 추출"""
        import re
        # KCD 코드 패턴 (A00-Z99)
        pattern = r'\b[A-Z]\d{2}(\.\d{1,2})?\b'
        return re.findall(pattern, text)


# 전역 인스턴스
rag_retriever = RAGRetriever()
