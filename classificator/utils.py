import requests
import json
import db
import os
import re


OLLAMA_API_URL = "http://localhost:11434/api/generate"  # ✅ 실제 Ollama 엔드포인트 주소
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts")


def classify_file(text, file_type, categories):
    """
    텍스트 기반 문서 분류
    - categories: 리스트, 가능한 카테고리
    - 출력은 반드시 하나의 category 문자열
    """
    if not categories:
        return "error", {"category": "categories is empty"}
    categories = list(categories)

    try:
        # ✅ 튜닝 데이터 형식과 동일한 인스트럭션 구조로 정리
        instruction = (
            f"다음 문서를 [{', '.join(categories)}] 카테고리 안에서 분류해줘."
        )

        system_prompt = f"""
            너는 문서 카테고리 분류를 수행하는 AI야.
            입력으로 주어진 문서는 하나의 카테고리에만 속할 수 있어.
            카테고리 목록은 다음과 같아:
            {', '.join(categories)}

            규칙:
            1. 반드시 위 목록 중 하나만 고른다.
            2. 출력은 반드시 JSON 형식으로 한다.
            3. 설명, 따옴표, 추가 텍스트, 영어 번역 절대 포함하지 말 것.
        """

        end_prompt = (
            '''
            지금까지의 내용을 바탕으로 category 키만 포함한 JSON을 출력해.
            그 외의 설명, 문장, 코드블록, 따옴표 등은 절대 추가하지 마.
            {
            "category": "category"
            }
            무조건 이 형식에 맞춰서 반환해줘
            '''
        )

        # ✅ 튜닝 구조에 맞춘 실제 프롬프트
        full_prompt = (
            f"{{\"instruction\": \"{instruction}\", \"input\": \"{text}\"}}\n\n"
            f"{system_prompt}\n\n{end_prompt}"
        )

        payload = {
            "model": "gemma3:1b",
            "prompt": full_prompt,
            "max_tokens": 128,
            "temperature": 0,
            "stream": False
        }

        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        raw_text = response.json().get("response", "").strip()
        print("[DEBUG] raw_text:", raw_text)

        # 코드블록 제거
        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            raw_text = match.group(1)
        raw_text = raw_text.strip()

        # JSON 파싱
        try:
            data = json.loads(raw_text)
            category = data.get("category")
        except:
            print("[WARN] JSON 파싱 실패")
            return "error", {"category": ""}

        # 카테고리 검증
        if category not in categories:
            return "error", {"category": category}

    except Exception as e:
        return "error", {"category": f"error: {e}"}

    return "done", category


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
