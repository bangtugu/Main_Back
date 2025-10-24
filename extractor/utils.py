import os
import subprocess
import requests
import db
from extract_pdf import extract
from image_ocr import run_ocr

SUPPORTED_EXTENSIONS = {"pdf", "hwp", "docx", "pptx", "xlsx",
                        "jpg", "jpeg", "png", "txt"}
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
CLASSFICATOR_DIR = 'http://localhost:8002/new_file/'
LIBREOFFICE_PATH = r"C:\\Program Files\\LibreOffice\\program\\soffice.exe"


def convert_to_pdf(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        LIBREOFFICE_PATH,
        "--headless",
        "--convert-to", "pdf",
        input_path,
        "--outdir", output_dir
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Windows 전용
        )
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(output_dir, f"{base_name}.pdf")
    except subprocess.CalledProcessError as e:
        # 상세 로그 출력(또는 파일에 저장)
        print(f"[ERROR] LibreOffice conversion failed: returncode={e.returncode}")
        print("[ERROR] stdout:", e.stdout)
        print("[ERROR] stderr:", e.stderr)
        # 필요하면 e.stderr를 DB의 ERROR_MESSAGE로 저장하게 반환
        return None
    except FileNotFoundError:
        print("[ERROR] soffice executable not found at:", LIBREOFFICE_PATH)
        return None


def handle_files(files: list):
    print(files)
    target_lst = []
    for file_id, file_type in files:
        if file_type not in SUPPORTED_EXTENSIONS:
            print(f"[SKIP] Unsupported file: {file_id}.{file_type}")
            continue
        target_lst.append([file_id, file_type])

    # 변환 시작 상태 DB 기록
    db.start_extract_bulk([f[0] for f in target_lst])
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    result = []

    for file_id, file_type in target_lst:
        try:
            file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_type}")
            txt_path = os.path.join(EXTRACT_DIR, f"{file_id}_extracted.txt")
            text = ""

            if file_type == "txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            elif file_type == "pdf":
                with open(file_path, "rb") as f:
                    pdf_bytes = f.read()
                text = extract(pdf_bytes)
            elif file_type in {"jpg", "jpeg", "png"}:
                text = run_ocr(file_path)
            else:
                pdf_path = convert_to_pdf(file_path, UPLOAD_DIR)
                print('[PDFPATH]', pdf_path)
                if pdf_path:
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    text = extract(pdf_bytes)
                else:
                    print(f"[WARN] Skipping extraction for file {file_id}")
                    continue

            with open(txt_path, "w", encoding="utf-8") as out:
                out.write(text)

            db.done_extract(file_id)
            result.append({"FILE_ID": file_id, "FILE_TYPE": file_type})
        except Exception as e:
            print('[ERROR]', e)

    # ✅ JSON 형태로 POST
    if result:
        requests.post(CLASSFICATOR_DIR, json={"files": result}, timeout=None)
