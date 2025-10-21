import os
import shutil
import db  # DB 기록용

# 업로드 저장 디렉토리
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def process_file(file_obj, start_index: int):
    """
    PDF 파일 저장 + DB 기록
    :param file_obj: UploadFile 객체
    :param start_index: main.py에서 관리하는 current_file_index
    :return: 마지막 index
    """
    current_index = start_index
    filename = file_obj.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext != ".pdf":
        # PDF가 아니면 처리하지 않고 인덱스 그대로 반환
        return current_index

    # 인덱스 증가
    current_index += 1

    # 저장할 파일 경로
    save_name = f"{current_index}.pdf"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    # 파일 저장
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file_obj.file, f)

    # DB 기록
    db.insert_file_record(current_index, filename)

    return current_index
