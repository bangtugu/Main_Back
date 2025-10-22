import os
from .extract_pdf import extract_pdf_text
from .extract_hwp import extract_hwp_text
from .extract_msoffice import extract_office_text
from .image_ocr import run_ocr
import requests
import db
import extract_hwp, extract_msoffice, extract_pdf, image_ocr
# from db_module import save_extraction_result  # 실제 DB 연동 시 주석 해제

SUPPORTED_EXTENSIONS = {".pdf", ".hwp", ".docx", ".pptx", ".xlsx",
                        ".jpg", ".jpeg", ".png", ".txt"}
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
CLASSFICATOR_DIR = 'http://localhost:8002/new_file/'


def handle_files(files):

    target_lst = []
    for file in files:
        file_id = file['FILE_ID']
        file_type = file['FILE_TYPE']
        # 리스트 맨 끝을 꺼냄 → LIFO
        if file_type not in SUPPORTED_EXTENSIONS:
            print(f"[SKIP] Unsupported file: {file_id}")
            continue
        
        target_lst.append([file_id, file_type])
    
    # 추출 시작 db 기록
    db.start_extract_bulk([f[0] for f in target_lst])

    # 파일별 추출
    for file_id, file_type in target_lst:

        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_type}")
        txt_path = os.path.join(EXTRACT_DIR, f"{file_id}_extracted.txt")

        if file_type == ".pdf":
            text = extract_pdf.extract(file_path)
        elif file_type == ".hwp":
            text = extract_hwp.extract(file_path)
        elif file_type in [".docx", ".pptx", ".xlsx"]:
            text = extract_msoffice.extract(file_path, file_type)
        elif file_type in [".jpg", ".jpeg", ".png"]:
            text = image_ocr.run_ocr(file_path)
        elif file_type == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        
        with open(txt_path, "w", encoding="utf-8") as out:
            out.write(text)

        # 추출 완료 db 기록
        db.done_extract(file_id)
    
    requests.post(CLASSFICATOR_DIR, json=target_lst, timeout=None)