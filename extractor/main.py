from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import requests, threading
import db, utils
import uvicorn

app = FastAPI(title="Extract_Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/new_file/")
async def new_file(file_ids: list[int]):
    utils.going_extract(file_ids)
    return {"status": "dispatched", "file_ids": file_ids}


def dispatch_unextracted_files():
    file_ids = db.get_unprocessed_files()
    if not file_ids:
        print("[INFO] No unextracted files found.")
        return

    print(f"[INFO] Found {len(file_ids)} unextracted files. Dispatching...")
    utils.going_extract(file_ids)


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
