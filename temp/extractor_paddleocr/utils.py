import os
import db  # DB 기록용
import pdftotext
from typing import List
import requests

# 업로드 저장 디렉토리
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts/paddleocr")
TARGET_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(EXTRACT_DIR, exist_ok=True)


def process_files_and_notify(file_ids: List[int]):
    """
    파일 추출 실행 후 완료된 ID를 Briefer 서버에 전달
    """
    for file_id in file_ids:
        try:
            run_extraction(file_id)
        except Exception as e:
            print(f"❌ [FILE {file_id}] 추출 실패: {e}")


def run_extraction(file_id: int):
    """
    file_id 기반으로 PDF → OCR → TXT 저장 → DB 갱신
    uploaded_files/{file_id}.pdf → extracted_texts/{file_id}.txt
    """
    try:
        pdf_path = os.path.join(TARGET_DIR, f"{file_id}.pdf")
        txt_path = os.path.join(EXTRACT_DIR, f"{file_id}.txt")

        print(f"📄 [{file_id}] OCR 시작")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # OCR 실행
        extracted_text = pdftotext.pdf_to_text_with_ocr(pdf_bytes)

        # 텍스트 파일로 저장
        with open(txt_path, "w", encoding="utf-8") as out:
            out.write(extracted_text)

        print(f"✅ [{file_id}] OCR 완료 → {txt_path}")

        # DB에 처리 완료 갱신
        db.update_extracted_text(file_id)
        print(f"🗂️ [{file_id}] DB 갱신 완료")

    except Exception as e:
        print(f"❌ [{file_id}] 처리 중 오류:", e)