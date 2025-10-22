from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
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

check_set = set()


@app.post("/new_file/")
async def new_file(files):
    utils.handle_files(files)
    return {"status": "dispatched", "files": files}


def dispatch_unclassficated_files():
    global check_set
    files = db.get_unprocessed_files()
    if not files:
        print("[INFO] No unextracted files found.")
        check_set = set()
        return

    temp_set = set()
    temp_lst = []
    for file in files:
        if file["IS_CLASSFICATION"] and file["FILE_ID"] not in check_set:
            temp_set.add(file["FILE_ID"])
        else:
            temp_lst.append([file["FILE_ID"], file["FILE_TYPE"]])
    
    check_set = temp_set
    print(f"[INFO] Found {len(temp_lst)} unextracted files. Dispatching...")
    utils.handle_files(temp_lst)


# ==============================
# APScheduler 설정
# ==============================
scheduler = BackgroundScheduler()
# 5분마다 dispatch_unextracted_files 호출
scheduler.add_job(dispatch_unclassficated_files, 'interval', minutes=5)
scheduler.start()

# FastAPI 종료 시 스케줄러 종료
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


if __name__ == "__main__":
    print("[INFO] Extract Manager initializing...")
    try:
        dispatch_unclassficated_files()  # 앱 시작 시 한 번 실행
    except Exception as e:
        print(f"[ERROR] Failed to dispatch unextracted files: {e}")

    print("[INFO] Starting Extract Manager API on port 8001...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
