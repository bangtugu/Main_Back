import requests
import json
import db
import os
import re


OLLAMA_API_URL = "http://localhost:11434/api/generate"  # ✅ 실제 Ollama 엔드포인트 주소
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts")


import requests
import json
import re

def classify_file(text, file_type, categories):
    """
    텍스트 기반 문서 분류
    - categories: 리스트, 가능한 카테고리
    - 출력은 반드시 하나의 category 문자열
    """
    if not categories:
        return "error", {"category": "categories is empty"}

    try:
        system_prompt = f"""
            너는 문서 분류 AI야.
            제공된 텍스트를 보고 반드시 아래 카테고리 중 하나만 선택해서 JSON 형태로 출력해.
            가능한 카테고리: {categories}
            반드시 목록 외의 값을 쓰지 말 것.
            출력은 JSON만 허용하며, 다른 텍스트나 설명은 포함하지 마.
            파일 원본 확장자: {file_type}
            예시 출력: {{"category": "{categories[0]}"}} 
            """
        end_prompt = (
            "지금까지 내용을 바탕으로 category 키만 포함한 JSON을 출력해. "
            "다른 텍스트나 따옴표, 설명 금지."
        )

        payload = {
            "model": "gemma3:1b",
            "prompt": f"{system_prompt}\n{text}\n{end_prompt}",
            "max_tokens": 300,
            "temperature": 0,   # 무작위 출력 줄이기
            "stream": False
        }

        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()

        raw_text = response.json().get("response", "")
        print(raw_text)
        # 정규식으로 JSON 부분만 추출
        match = re.search(r'\{"category"\s*:\s*".*?"\}', raw_text)
        print(match.group())
        print(json.loads(match.group()))
        try:
            classification_json = json.loads(match.group())
        except:
            classification_json = {"category": "기타"}

        if classification_json["category"] not in categories:
            classification_json["category"] = "기타"

    except Exception as e:
        return "error", {"category": f"error: {e}"}

    return "done", classification_json["category"]



def handle_files(files):
    """
    files: [(file_id, file_type), ...]
    폴더 단위로 그룹화해서 classification 수행
    """

    # 1️⃣ classification 시작 DB 기록
    db.start_classification_bulk([f[0] for f in files])
    print("[INFO] Files to classify:", files)

    # 2️⃣ 파일별 folder_id 한 번에 가져오기
    file_ids = [f[0] for f in files]
    file_folder_map = db.get_folder_ids_for_files(file_ids)
    # 반환 예시: {1: 101, 2: 101, 3: 102, ...}

    # 3️⃣ 폴더별로 파일 묶기
    from collections import defaultdict
    folder_files = defaultdict(list)
    for file_id, file_type in files:
        folder_id = file_folder_map.get(file_id)
        if folder_id is None:
            print(f"[WARN] folder_id not found for file {file_id}")
            continue
        folder_files[folder_id].append((file_id, file_type))

    # 4️⃣ 폴더 단위로 classification 수행
    for folder_id, files_in_folder in folder_files.items():
        # 폴더 카테고리 가져오기 (리스트)
        categories = db.get_categories_for_folder(folder_id)
        print(f"[INFO] Folder {folder_id}, categories: {categories}, files: {files_in_folder}")
        if not categories:
            print(f"[INFO] folder {folder_id}\'s categories is None.")
            for file_id, _ in files_in_folder:
                db.done_classification(file_id, 'Null')
            continue

        for file_id, file_type in files_in_folder:
            try:
                txt_path = os.path.join(EXTRACT_DIR, f"{file_id}_extracted.txt")
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()

                # classify_file은 category 리스트 인자로 전달
                result, category = classify_file(text, file_type, categories)
                print(f"[INFO] File {file_id}: {result}")

                if result == "done":
                    db.done_classification(file_id, category)
                else:
                    print(f"[ERROR] {file_id} classfication FAILED")
                    db.error_classification(file_id)

            except Exception as e:
                print(f"[ERROR] File {file_id}: {e}")
                db.error_classification(file_id)
