from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import db, utils, uvicorn
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import List


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
async def upload_files(
    background_tasks: BackgroundTasks,
    user_id: int = Form(...),
    folder_id: int = Form(...),
    files: List[UploadFile] = File(...)
):
    global current_file_index
    current_file_index, results = utils.upload_files(
        user_id, folder_id, files, current_file_index, background_tasks
    )
    return JSONResponse(content={"status": "upload_complete", "uploaded_files": results})


@app.get("/folders/{user_id}")
async def get_user_folders(user_id: int):
    """
    특정 유저(user_id)의 폴더 목록과 폴더 안 파일 개수를 반환
    """
    folders = db.get_user_folders_with_details(user_id)
    return JSONResponse(content={"folders": folders})


@app.get("/files/{folder_id}")
async def get_folder_categories_and_files(folder_id: int):
    """
    특정 폴더(folder_id)의 파일 목록 반환
    """
    files = db.get_files_in_folder(folder_id)
    categories = db.get_categories_in_folder(folder_id)
    return JSONResponse(content={"files": files, "categories": categories})


@app.post("/folders/create/")
async def create_folder(user_id: int = Form(...), folder_name: str = Form(...)):
    folder_id = db.create_folder(user_id, folder_name)
    return JSONResponse(content={"status": "success", "folder_name": folder_name})


@app.put("/folders/{folder_id}/rename/")
async def rename_folder(folder_id: int, new_name: str = Form(...)):
    success = db.rename_folder(folder_id, new_name)
    if success:
        return JSONResponse(content={"status": "success"})
    else:
        return JSONResponse(content={"status": "failed", "message": "Folder not found"})


@app.post("/folders/{folder_id}/category/")
async def create_folder_category(folder_id: int, category: str):
    db.create_folder_category(folder_id, category)
    return JSONResponse(content={"status": "success", "created_category": category})


@app.delete("/folders/{folder_id}/category/")
async def delete_folder_category(folder_id: int, category: str):
    db.update_folder_categories(folder_id, category)
    return JSONResponse(content={"status": "success", "deleted_categories": category})


@app.delete("/folders/{folder_id}")
async def delete_folder(folder_id: int):
    """
    폴더 및 하위 데이터(파일, 카테고리 등) 삭제
    """
    try:
        db.delete_folder(folder_id)
        return JSONResponse(content={"status": "success", "message": f"Folder {folder_id} deleted"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        # reload=True
    )