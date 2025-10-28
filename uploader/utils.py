# utils.py
import os
import shutil
import zipfile
import db
from fastapi import BackgroundTasks

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

EXTRACTOR_URL = "http://localhost:8001/new_file/"
SUPPORTED_EXTENSIONS = {".pdf", ".hwp", ".docx", ".pptx", ".xlsx",
                        ".jpg", ".jpeg", ".png", ".zip", ".txt"}


def send_to_extractor(recorded):
    """
    백그라운드에서 extractor 호출
    """
    import requests
    try:
        requests.post(EXTRACTOR_URL, json={"files": recorded}, timeout=None)
        print("[INFO] Extractor request sent")
    except Exception as e:
        print(f"[ERROR] extractor request failed: {e}")


def upload_files(user_id, folder_id, files, current_file_index, background_tasks: BackgroundTasks):
    """
    파일 업로드 처리 후, extractor 호출을 백그라운드에서 실행
    """
    results = {}
    recorded = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        try:
            save_path = os.path.join(UPLOAD_DIR, f"{current_file_index}{ext}")
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            record_type = ext.replace('.', '') if ext in SUPPORTED_EXTENSIONS else "unsupported"
            db.insert_file_record(current_file_index, file.filename, record_type, user_id, folder_id)
            db.upload_file_log(file.filename)

            recorded.append({'FILE_ID': current_file_index, 'FILE_TYPE': record_type})
            results[file.filename] = "success"
            current_file_index += 1

            # zip 파일 처리
            if ext == ".zip":
                with zipfile.ZipFile(save_path, 'r') as zip_ref:
                    for inner_file in zip_ref.namelist():
                        inner_ext = os.path.splitext(inner_file)[1].lower()
                        inner_save_path = os.path.join(UPLOAD_DIR, f"{current_file_index}{inner_ext}")
                        zip_ref.extract(inner_file, UPLOAD_DIR)
                        os.rename(os.path.join(UPLOAD_DIR, inner_file), inner_save_path)

                        if inner_ext not in SUPPORTED_EXTENSIONS or inner_ext == ".zip":
                            record_type = "unsupported"
                        else:
                            record_type = inner_ext.replace('.', '')

                        db.insert_file_record(current_file_index, inner_file, record_type, user_id, folder_id)
                        recorded.append({'FILE_ID': current_file_index, 'FILE_TYPE': record_type})
                        current_file_index += 1

        except Exception as e:
            results[file.filename] = f"fail: {str(e)}"

    # 백그라운드에서 extractor 호출
    background_tasks.add_task(send_to_extractor, recorded)

    return current_file_index, results
