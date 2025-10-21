import os
import tempfile
import shutil
import zipfile
import db

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 지원 확장자
SUPPORTED_EXTENSIONS = {".pdf", ".hwp", ".docx", ".pptx", ".xlsx",
                        ".jpg", ".jpeg", ".png", ".zip"}


def simple_upload_files(user_id, files, current_file_index):
    results = {}

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()

        try:
            # 공통: 파일 저장
            save_path = os.path.join(UPLOAD_DIR, f"{current_file_index}{ext}")
            with open(save_path, "wb") as f:
                f.write(file.file.read())

            # -----------------------------
            # 지원 안 되는 확장자 or zip은 단순 저장만
            # -----------------------------
            if ext not in SUPPORTED_EXTENSIONS:
                db.insert_file_record(current_file_index, file.filename, "unsupported", user_id)
                results[file.filename] = "saved_only"
                current_file_index += 1
                continue

            # -----------------------------
            # 지원하는 확장자: 처리 및 ExtractManager 알림
            # -----------------------------
            db.insert_file_record(current_file_index, file.filename, ext, user_id)
            results[file.filename] = "success"
            current_file_index += 1

        except Exception as e:
            results[file.filename] = f"fail: {str(e)}"

    return current_file_index, results


# def process_file(file_obj, start_index: int):
#     """
#     파일 저장 + ZIP 처리 + DB 기록 (재귀 처리 포함)
#     start_index: main.py에서 관리하는 current_file_index
#     return: 마지막 index
#     """
#     current_index = start_index

#     def handle_file(f_path, f_name):
#         nonlocal current_index
#         ext = os.path.splitext(f_name)[1].lower()

#         # ZIP이면 재귀 처리
#         if ext == ".zip":
#             extract_dir = tempfile.mkdtemp(prefix="unzipped_")
#             with zipfile.ZipFile(f_path, 'r') as z:
#                 z.extractall(extract_dir)

#             for root, _, files in os.walk(extract_dir):
#                 for inner_name in files:
#                     inner_path = os.path.join(root, inner_name)
#                     handle_file(inner_path, inner_name)

#             os.remove(f_path)  # 원본 ZIP 제거
#         else:
#             # current_index 증가 + 파일 이름 변경
#             current_index += 1
#             new_name = f"file_{current_index}{ext}"
#             save_path = os.path.join(UPLOAD_DIR, new_name)

#             # 파일 저장 (file_obj가 아닌 실제 경로 사용)
#             shutil.move(f_path, save_path)

#             # 지원 확장자만 DB 기록
#             if ext in SUPPORTED_EXTENSIONS:
#                 db.insert_file_record(current_index, f_name, new_name)

#     # 최상위 파일 처리
#     # 일반 파일이면 임시 경로에 저장 후 handle_file 호출
#     top_file_path = os.path.join(UPLOAD_DIR, f"temp_{current_index}" + os.path.splitext(file_obj.filename)[1])
#     with open(top_file_path, "wb") as f:
#         shutil.copyfileobj(file_obj.file, f)

#     handle_file(top_file_path, file_obj.filename)

#     # 마지막 index 반환
#     return current_index
