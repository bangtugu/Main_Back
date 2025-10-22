# utils.py
import os
import shutil
import zipfile
import db
import requests

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

EXTRACTOR_URL = "http://localhost:8001/new_file/"
SUPPORTED_EXTENSIONS = {".pdf", ".hwp", ".docx", ".pptx", ".xlsx",
                        ".jpg", ".jpeg", ".png", ".zip", ".txt"}

def simple_upload_files(user_id, files, current_file_index):
    """
    파일 업로드 후 DB 기록
    - ZIP 파일은 내부 자동 추출
    - 내부 파일도 실제 저장 + 개별 DB 기록
    - parent_file_id 연결 없음
    """
    results = {}
    recorded = {}

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()

        try:
            # 1. 상위 파일 서버에 저장
            save_path = os.path.join(UPLOAD_DIR, f"{current_file_index}{ext}")
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # 2. DB 기록 (상위 파일)
            record_type = ext.replace('.', '') if ext in SUPPORTED_EXTENSIONS else "unsupported"
            db.insert_file_record(current_file_index, file.filename, record_type, user_id, save_path)
            recorded.append({'FILE_ID': current_file_index, 'FILE_TYPE': record_type})
            results[file.filename] = "success"
            current_file_index += 1
            
            # 3. ZIP 내부 파일 처리
            if ext == ".zip":
                with zipfile.ZipFile(save_path, 'r') as zip_ref:
                    for inner_file in zip_ref.namelist():
                        inner_ext = os.path.splitext(inner_file)[1].lower()
                        inner_save_path = os.path.join(UPLOAD_DIR, f"{current_file_index}{inner_ext}")

                        # 실제 파일 모두 추출
                        zip_ref.extract(inner_file, UPLOAD_DIR)
                        extracted_path = os.path.join(UPLOAD_DIR, inner_file)
                        os.rename(extracted_path, inner_save_path)

                        # DB 기록
                        if inner_ext not in SUPPORTED_EXTENSIONS or inner_ext == ".zip":
                            record_type = "unsupported"
                        else:
                            record_type = inner_ext.replace('.', '')

                        db.insert_file_record(current_file_index, inner_file, record_type, user_id, inner_save_path)
                        recorded.append({'FILE_ID': current_file_index, 'FILE_TYPE': record_type})
                        current_file_index += 1

        except Exception as e:
            results[file.filename] = f"fail: {str(e)}"

    requests.post(EXTRACTOR_URL, json=recorded, timeout=None)
    return current_file_index, results
