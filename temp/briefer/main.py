from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
import utils, db
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(title="Briefer")

origins = [
    "http://localhost:3000",  # React 개발서버 주소
    "http://localhost:8001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def handle_files(file_ids: List[int]):
    for file_id in file_ids:
        utils.run_brief(file_id)

def dispatch_unprocessed_files():
    """주기적으로 미처리 파일 체크 및 요약"""
    unprocessed_ids = db.get_unprocessed_files()
    if unprocessed_ids:
        print(f"🟢 Briefer: {len(unprocessed_ids)}개 미처리 파일 요약 시작")
        handle_files(unprocessed_ids)
    else:
        print("✅ Briefer: 미처리 파일 없음")

scheduler = BackgroundScheduler()
scheduler.add_job(dispatch_unprocessed_files, 'interval', minutes=5)

@app.on_event("startup")
def startup_event():
    print("🟢 Briefer 서버 시작: 스케줄러 가동")
    dispatch_unprocessed_files()  # 서버 시작 시 바로 한 번 실행
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    print("🔴 Briefer 서버 종료: 스케줄러 중단")
    scheduler.shutdown()

@app.post("/extracted_file/")
def new_files(file_ids: List[int], background_tasks: BackgroundTasks):
    """새로 들어온 파일 ID 리스트를 받아 순차 요약"""
    background_tasks.add_task(handle_files, file_ids)
    return {"status": "done"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True
    )
