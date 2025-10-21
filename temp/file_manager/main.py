from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, os, requests
from utils import process_file
import db

app = FastAPI(title="File Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요 시 도메인 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXTRACT_MANAGER_URL = "http://localhost:8001/new_file/"

# 저장 경로 설정
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts")
SUMMARY_DIR = os.path.join(BASE_DIR, "summary_texts")
OCR_TYPES = ["pytesseract", "easyocr", "paddleocr"]

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)

# 서버 시작 시 DB에서 MAX FILE_ID 조회 후 초기화
current_file_index = db.get_max_file_id() or 0


# ✅ 파일 업로드
@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    global current_file_index
    results = {}
    dispatched_file_ids = []

    for file in files:
        filename = file.filename
        ext = filename.split(".")[-1].lower()
        if ext != "pdf":
            results[filename] = "skipped (not PDF)"
            continue

        try:
            # PDF 파일 저장 및 DB 기록
            current_file_index = process_file(file, current_file_index)
            results[filename] = "success"
            dispatched_file_ids.append(current_file_index)
        except Exception as e:
            results[filename] = f"fail: {str(e)}"

    # ExtractManager에 전달
    if dispatched_file_ids:
        try:
            payload = dispatched_file_ids
            requests.post(EXTRACT_MANAGER_URL, json=payload, timeout=5)
            print(f"✅ ExtractManager notified for file_ids={dispatched_file_ids}")
        except Exception as notify_err:
            print(f"⚠️ Failed to notify ExtractManager: {notify_err}")

    return JSONResponse(content={"uploaded_files": results})


# ✅ 파일 목록 조회 (DB 기반)
@app.get("/files/")
def list_files(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    search: str = Query(None, description="검색어 (제목/키워드)")
):
    result = db.get_file_page(page, limit, search)
    return JSONResponse(result)


@app.get("/file/{file_id}")
def get_ocr_texts(file_id: int):
    result = {}
    for ocr in OCR_TYPES:
        txt_path = os.path.join(EXTRACT_DIR, ocr, f"{file_id}.txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                result[ocr] = f.read()
        else:
            result[ocr] = ""  # 파일 없으면 빈 문자열
    return {"file_id": file_id, "ocr_texts": result}


@app.get("/search/")
def search_files(keyword: str):
    """
    DB에서 해당 문자가 들어간 파일 검색
    """
    files = db.get_files_by_keyword(keyword)
    return JSONResponse(content={"files": files})




# ✅ 원본 PDF 다운로드
@app.get("/download/pdf/{file_id}")
def download_pdf(file_id: int):
    """
    특정 파일 ID의 PDF 다운로드
    """
    title = db.get_file_name(file_id)
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    if not os.path.exists(pdf_path):
        return JSONResponse(content={"error": "PDF not found"}, status_code=404)
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{title}")


# ✅ 추출 텍스트 다운로드
@app.get("/download/txt/{file_id}/{ocr_type}")
def download_txt(file_id: int, ocr_type: str):
    """
    특정 파일 ID의 특정 OCR TXT 다운로드
    """
    title = db.get_file_name(file_id)

    # f-string 사용 시 따옴표와 괄호 확인
    txt_path = os.path.join(EXTRACT_DIR, ocr_type, f"{file_id}.txt")
    
    if not os.path.exists(txt_path):
        return JSONResponse(content={"error": "Extract txt not found"}, status_code=404)
    
    return FileResponse(
        txt_path,
        media_type="text/plain",
        filename=f"{title}_{ocr_type}.txt"
    )


# ✅ 요약 텍스트 다운로드
@app.get("/download/summary/{file_id}")
def download_summary(file_id: int):
    """
    특정 파일 ID의 요약 TXT 다운로드
    """
    txt_path = os.path.join(SUMMARY_DIR, f"{file_id}_summary.txt")
    if not os.path.exists(txt_path):
        return JSONResponse(content={"error": "Summary not found"}, status_code=404)
    return FileResponse(txt_path, media_type="text/plain", filename=f"{file_id}_summary.txt")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
