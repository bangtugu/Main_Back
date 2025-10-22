import os
import subprocess
import requests
import db
from extract_pdf import extract  # 기존 PDF extractor
# 필요한 경우 이미지 OCR도 import
from image_ocr import run_ocr

SUPPORTED_EXTENSIONS = {".pdf", ".hwp", ".docx", ".pptx", ".xlsx",
                        ".jpg", ".jpeg", ".png", ".txt"}
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
CLASSFICATOR_DIR = 'http://localhost:8002/new_file/'


# LibreOffice 변환 함수
def convert_to_pdf(input_path, output_dir):
    try:
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", output_dir],
            check=True
        )
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(output_dir, f"{base_name}.pdf")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] LibreOffice conversion failed: {e}")
        return None


def handle_files(files: list):
    target_lst = []
    for file_id, file_type in files:

        if file_type not in SUPPORTED_EXTENSIONS:
            print(f"[SKIP] Unsupported file: {file_id}")
            continue
        
        target_lst.append([file_id, file_type])

    # 추출 시작 DB 기록
    db.start_extract_bulk([f[0] for f in target_lst])
    
    for file_id, file_type in target_lst:
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_type}")
        txt_path = os.path.join(EXTRACT_DIR, f"{file_id}_extracted.txt")
        text = ""

        if file_type == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif file_type == ".pdf":
            text = extract(file_path)
        elif file_type in {".jpg", ".jpeg", ".png"}:
            text = run_ocr(file_path)
        else:
            # PDF로 변환 후 추출
            pdf_path = convert_to_pdf(file_path, UPLOAD_DIR)
            if pdf_path:
                text = extract(pdf_path)
            else:
                print(f"[WARN] Skipping extraction for file {file_id}")
                continue

        # 추출 텍스트 저장
        os.makedirs(EXTRACT_DIR, exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as out:
            out.write(text)

        # 추출 완료 DB 기록
        db.done_extract(file_id)

    # Classificator 서버로 추출 완료 파일 전송
    requests.post(CLASSFICATOR_DIR, json=target_lst, timeout=None)
