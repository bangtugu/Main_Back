import os
from .extract_pdf import extract_pdf_text
from .extract_hwp import extract_hwp_text
from .extract_msoffice import extract_office_text
from .image_ocr import run_ocr
# from db_module import save_extraction_result  # 실제 DB 연동 시 주석 해제

SUPPORTED_EXTENSIONS = {".pdf", ".hwp", ".docx", ".pptx", ".xlsx",
                        ".jpg", ".jpeg", ".png"}

def is_supported(file_path):
    """지원되는 파일인지 확인"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS

def process_file(file_path):
    """
    파일 타입별 extractor 호출
    - PDF/HWP/Office: 텍스트 + 내부 이미지 OCR 포함
    - Standalone 이미지: OCR 독립 처리
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        if ext == ".pdf":
            text = extract_pdf_text(file_path)
        elif ext == ".hwp":
            text = extract_hwp_text(file_path)
        elif ext in [".docx", ".pptx", ".xlsx"]:
            text = extract_office_text(file_path)
        elif ext in [".jpg", ".jpeg", ".png"]:
            text = run_ocr(file_path)
        else:
            print(f"[SKIP] Unsupported file type: {file_path}")
            return

        # TODO: 추출 결과 DB에 저장
        # save_extraction_result(file_path, text)

        print(f"[EXTRACTED] {file_path} ({len(text)} chars)")

    except Exception as e:
        print(f"[FAIL] {file_path}: {str(e)}")

    return text

def process_file_list(file_list):
    """
    파일 리스트 순회하며 각 파일 추출 (LIFO)
    - DB에서 가져온 리스트 그대로 전달하면 utils에서 pop()으로 처리
    """
    while file_list:
        file_path = file_list.pop()  # 리스트 맨 끝을 꺼냄 → LIFO
        if not is_supported(file_path):
            print(f"[SKIP] Unsupported file: {file_path}")
            continue

        process_file(file_path)
