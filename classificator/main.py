from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import db, utils
import uvicorn

app = FastAPI(title="Classificator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

check_set = set()


@app.post("/new_file/")
async def new_file(request: dict):
    """
    extractor에서 전달된 파일 목록을 처리
    expected format:
    {
        "files": [
            {"FILE_ID": 1, "FILE_TYPE": "pdf"},
            {"FILE_ID": 2, "FILE_TYPE": "hwp"}
        ]
    }
    """
    json_files = request.get("files", [])
    print(json_files)
    files = [(f["FILE_ID"], f["FILE_TYPE"]) for f in json_files]

    utils.handle_files(files)  # 분류 처리 전용 utils 함수
    return {"status": "dispatched", "files": files}


def dispatch_unclassified_files():
    """
    DB에서 아직 분류되지 않은 파일 조회 후 처리
    """
    global check_set
    print('get unclassification files')
    files = db.get_unclassified_files()  # IS_CLASSiFICATION < 2인 파일
    print(files)
    temp_set = set()
    temp_lst = []
    for file_id, file_type, is_classification in files:
        if is_classification and file_id not in check_set:
            temp_set.add(file_id)
        else:
            temp_lst.append([file_id, file_type])
    print(check_set, temp_set, temp_lst)
    check_set = temp_set
    if not temp_lst:
        print("[INFO] No unclassified files found.")
    else:
        print(f"[INFO] Found {len(temp_lst)} unclassified files. Dispatching...")
        utils.handle_files(temp_lst)


# ==============================
# APScheduler 설정
# ==============================
scheduler = BackgroundScheduler()
scheduler.add_job(dispatch_unclassified_files, 'interval', minutes=1)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


if __name__ == "__main__":
    print("[INFO] Starting Classificator API on port 8002...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        # reload=True
    )
