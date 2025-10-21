import time, uvicorn
from .db import fetch_unprocessed_files
from .utils import process_file_list

CHECK_INTERVAL = 5  # 초 단위

def main():
    print("🟢 OCR 백그라운드 작업 시작...")
    while True:
        # DB에서 미추출 파일 조회
        unprocessed_files = fetch_unprocessed_files()
        if not unprocessed_files:
            print("No unprocessed files. 대기중...")
            time.sleep(CHECK_INTERVAL)
            continue

        # OCR 처리 및 DB 업데이트
        process_file_list(unprocessed_files)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
