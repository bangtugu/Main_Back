from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import requests, threading
import db
import uvicorn

app = FastAPI(title="Extract_Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OCR_SERVERS = {
    "pytesseract": "http://localhost:8002/extract/",
    "easyocr": "http://localhost:8003/extract/",
    "paddleocr": "http://localhost:8004/extract/"
}


def dispatch_to_ocr_servers(file_ids, ocr_type):
    server_url = OCR_SERVERS[ocr_type]

    def send_request():
        try:
            requests.post(server_url, json=file_ids, timeout=None)
            print(f"[INFO] {ocr_type} 서버에 {len(file_ids)}개 파일 전송 완료")
        except Exception as e:
            print(f"[ERROR] {ocr_type} 서버 전송 실패: {e}")

    threading.Thread(target=send_request).start()
    print(f"[INFO] {ocr_type} 서버로 백그라운드 전송 시작")


@app.post("/new_file/")
async def new_file(file_ids: list[int]):
    for ocr_type in OCR_SERVERS.keys():
        dispatch_to_ocr_servers(file_ids, ocr_type)
    return {"status": "dispatched", "file_ids": file_ids}


def dispatch_unextracted_files():
    unprocessed = db.get_unprocessed_files()
    if not unprocessed:
        print("[INFO] No unextracted files found.")
        return

    print(f"[INFO] Found {len(unprocessed)} unextracted files. Dispatching...")
    pytess_ids, easy_ids, paddle_ids = [], [], []

    for file_id, is_pytess, is_easy, is_paddle in unprocessed:
        if is_pytess == 0:
            pytess_ids.append(file_id)
        if is_easy == 0:
            easy_ids.append(file_id)
        if is_paddle == 0:
            paddle_ids.append(file_id)

    if pytess_ids:
        dispatch_to_ocr_servers(pytess_ids, 'pytesseract')
    if easy_ids:
        dispatch_to_ocr_servers(easy_ids, 'easyocr')
    if paddle_ids:
        dispatch_to_ocr_servers(paddle_ids, 'paddleocr')


# ==============================
# APScheduler 설정
# ==============================
scheduler = BackgroundScheduler()
# 5분마다 dispatch_unextracted_files 호출
scheduler.add_job(dispatch_unextracted_files, 'interval', minutes=5)
scheduler.start()

# FastAPI 종료 시 스케줄러 종료
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


if __name__ == "__main__":
    print("[INFO] Extract Manager initializing...")
    try:
        dispatch_unextracted_files()  # 앱 시작 시 한 번 실행
    except Exception as e:
        print(f"[ERROR] Failed to dispatch unextracted files: {e}")

    print("[INFO] Starting Extract Manager API on port 8001...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
