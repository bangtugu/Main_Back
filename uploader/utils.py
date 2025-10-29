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


def zip_handler(user_id, folder_id, zipfile_id, current_file_index, background_tasks):

    # db에서 불러오거나, 받거나
    ext = '.zip'
    results = {}
    extract_target_lst = []
    save_path = os.path.join(UPLOAD_DIR, f"{zipfile_id}{ext}")

    print(f'[UPLOAD] file {zipfile_id}.zip unzip')
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            try:
                inner_ext = os.path.splitext(file)[1].lower()
                inner_save_path = os.path.join(UPLOAD_DIR, f"{current_file_index}{inner_ext}")
                zip_ref.extract(file, UPLOAD_DIR)
                os.rename(os.path.join(UPLOAD_DIR, file), inner_save_path)

                record_type = inner_ext.replace('.', '') if inner_ext in SUPPORTED_EXTENSIONS else "unsupported"

                db.insert_file_record(current_file_index, file, record_type, user_id, folder_id)
                if record_type not in ('zip', 'unsupported'): 
                    extract_target_lst.append({'FILE_ID': current_file_index, 'FILE_TYPE': record_type})
                results[file] = "success"
                current_file_index += 1
            
            except Exception as e:
                print(e)
                results[file] = f"fail: {str(e)}"

    background_tasks.add_task(send_to_extractor, extract_target_lst)
    return current_file_index, results
    

def upload_files(user_id, folder_id, files, current_file_index, background_tasks: BackgroundTasks):
    """
    파일 업로드 처리 후, extractor 호출을 백그라운드에서 실행
    """
    results = {}
    extract_target_lst = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        try:
            save_path = os.path.join(UPLOAD_DIR, f"{current_file_index}{ext}")
            with open(save_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            record_type = ext.replace('.', '') if ext in SUPPORTED_EXTENSIONS else "unsupported"
            db.insert_file_record(current_file_index, file.filename, record_type, user_id, folder_id)
            # db.upload_file_log(file.filename)
            print(f'[UPLOAD] file {current_file_index} uploaded')

            if record_type not in ('zip', 'unsupported'): 
                extract_target_lst.append({'FILE_ID': current_file_index, 'FILE_TYPE': record_type})
            results[file.filename] = "success"
            current_file_index += 1

        except Exception as e:
            print(e)
            results[file.filename] = f"fail: {str(e)}"

    # 백그라운드에서 extractor 호출
    background_tasks.add_task(send_to_extractor, extract_target_lst)
    return current_file_index, results
