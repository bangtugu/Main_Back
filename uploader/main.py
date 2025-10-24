from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import db, utils, uvicorn
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="File Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 또는 프론트 도메인 입력
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST 등 허용
    allow_headers=["*"],
)

# 서버 시작 시 DB에서 MAX FILE_ID 조회 후 초기화
current_file_index = db.get_max_file_id() or 0
current_file_index += 1


@app.post("/upload/")
async def upload_files(user_id: int, files: list[UploadFile] = File(...)):
    global current_file_index
    current_file_index, results = utils.simple_upload_files(user_id, files, current_file_index)
    return JSONResponse(content={"uploaded_files": results})


@app.get("/files/")
async def get_files(user_id: int):
    result = db.get_user_files(user_id)
    return JSONResponse(content={"user_files": result})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )