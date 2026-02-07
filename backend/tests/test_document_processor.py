"""
문서 처리 서비스 테스트
"""
import pytest
import os
import tempfile
from services.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """문서 처리기 테스트"""

    def test_supported_extensions(self):
        """지원 확장자 확인"""
        extensions = DocumentProcessor.get_supported_extensions()

        # 필수 형식 확인
        assert '.txt' in extensions
        assert '.pdf' in extensions
        assert '.docx' in extensions
        assert '.xlsx' in extensions

    def test_extract_from_txt(self):
        """텍스트 파일 추출 테스트"""
        processor = DocumentProcessor()

        # 임시 텍스트 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("테스트 텍스트\n여러 줄의 내용입니다.")
            temp_path = f.name

        try:
            result = processor.extract_text(temp_path, "test.txt")

            assert result['text'] is not None
            assert '테스트 텍스트' in result['text']
            assert result['page_count'] == 1
            assert result['error'] is None
        finally:
            os.unlink(temp_path)

    def test_extract_from_txt_korean_encoding(self):
        """한글 인코딩 테스트 (CP949/EUC-KR)"""
        processor = DocumentProcessor()

        # EUC-KR 인코딩으로 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='euc-kr') as f:
            f.write("한글 테스트입니다.")
            temp_path = f.name

        try:
            result = processor.extract_text(temp_path, "test_kr.txt")

            assert '한글' in result['text'] or '테스트' in result['text']
        finally:
            os.unlink(temp_path)

    def test_unsupported_format(self):
        """지원하지 않는 형식 테스트"""
        processor = DocumentProcessor()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            result = processor.extract_text(temp_path, "test.xyz")

            assert result['error'] is not None
            assert result['text'] == ''
        finally:
            os.unlink(temp_path)

    def test_sanitize_text(self):
        """텍스트 정제 테스트"""
        text = "  테스트   \n\n\n  텍스트  \n\n  입니다.  "
        sanitized = DocumentProcessor.sanitize_text(text)

        # 연속 공백이 줄어들고, 연속 개행이 정리되어야 함
        assert '  ' not in sanitized  # 연속 공백 없음
        assert '\n\n' in sanitized  # 문단 구분은 유지

    def test_pdf_with_pypdf2(self):
        """PDF 처리 테스트 (PyPDF2)"""
        processor = DocumentProcessor()

        # PyPDF2 설치 확인
        try:
            import PyPDF2
        except ImportError:
            pytest.skip("PyPDF2 not installed")

        # 실제 PDF 파일이 없으므로 형식만 확인
        assert '.pdf' in DocumentProcessor.SUPPORTED_PDF_FORMATS

    def test_process_document_integration(self):
        """문서 처리 통합 테스트"""
        processor = DocumentProcessor()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            content = "# 문서 제목\n\n## 내용\n\n이것은 테스트 문서입니다."
            f.write(content)
            temp_path = f.name

        try:
            result = processor.process_document(temp_path, "test_doc.txt")

            assert result['text'] is not None
            assert '문서 제목' in result['text']
            assert result['error'] is None
            assert result['metadata']['filename'] == 'test_doc.txt'
        finally:
            os.unlink(temp_path)

    def test_empty_file(self):
        """빈 파일 처리 테스트"""
        processor = DocumentProcessor()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = processor.process_document(temp_path, "empty.txt")

            # 빈 파일도 처리는 가능해야 함
            assert result['text'] == ''
        finally:
            os.unlink(temp_path)


def test_extract_text_from_file():
    """편의 함수 테스트"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("편의 함수 테스트")
        temp_path = f.name

    try:
        from services.document_processor import extract_text_from_file

        text, metadata = extract_text_from_file(temp_path, "test.txt")

        assert '편의 함수 테스트' in text
        assert metadata['filename'] == 'test.txt'
    finally:
        os.unlink(temp_path)
