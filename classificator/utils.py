import requests
import json
import db
import os
import re


OLLAMA_API_URL = "http://localhost:11434/api/generate"  # ✅ 실제 Ollama 엔드포인트 주소
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts")


def classify_file(text, file_type):
    """
    텍스트 기반 문서 분류
    - 출력은 반드시 JSON: {"category": "회의록"} 형태
    """
    try:
        system_prompt = (
            "너는 문서 분류 AI야. 제공된 텍스트를 보고 다음 중 하나를 category 키로 가진 JSON만 출력해:\n"
            "회의록, 일부개정법률안, 입법, 법률안, 기타.\n"
            f"원본 파일 확장자: {file_type}\n"
            "반드시 JSON 형식만 출력. 다른 텍스트나 따옴표 없이 출력.\n"
            "예시: {\"category\": \"법률안\"}"
        )

        end_prompt = (
            "지금까지의 내용을 바탕으로 문서 형식을 JSON으로 반환해. "
            "출력은 category 키만 포함하고, 다른 텍스트는 포함하지 마."
        )

        payload = {
            "model": "gemma3:1b",
            "prompt": f"{system_prompt}\n{text}\n{end_prompt}",
            "max_tokens": 300,
            "stream": False
        }
        print('before gemma')
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        # resp_json = response.json()
        # print(2, resp_json)
        # raw_text = resp_json.get("response", "")
        # print(3, raw_text)
        # clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        # print(4, clean_text)
        # try:
        #     classification_json = json.loads(clean_text)
        # except json.JSONDecodeError:
        #     classification_json = {"category": "알 수 없음"}
        # print(5, classification_json)


        # print(raw_text)

        # print('after gemma')
        # # print(raw_text)
        # # 🔹 JSON 안전 파싱
        # match = re.search(r"\{.*?\}", raw_text, re.DOTALL)
        # print('match')
        # if match:
        #     print(match)
        #     classification_json = json.loads(match.group())
        # else:
        #     classification_json = {"category": "알 수 없음"}
        # print('end')


        resp_json = response.json()
        print(2, resp_json)
        raw_text = resp_json.get("response", "")
        print(3, raw_text)
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        print(4, clean_text)
        try:
            classification_json = json.loads(clean_text)
        except json.JSONDecodeError:
            classification_json = {"category": "알 수 없음"}
        print(5, classification_json)

    except Exception as e:
        return "error", {"category": f"error: {e}"}

    return "done", classification_json["category"]

    

def classify_text(text, instruction=None):
    """
    텍스트를 Gemma3 모델로 분류
    """
    payload = {
        "model": "gemma3",
        "prompt": text if not instruction else f"{instruction}\n\n{text}",
        "max_tokens": 512
    }
    try:
        resp = requests.post(OLLAMA_API_URL, json=payload)
        resp.raise_for_status()
        completion = resp.json().get("completion", "").strip()
        return completion
    except Exception as e:
        print(f"[ERROR] Ollama classify failed: {e}")
        return None


def handle_files(files):
    
    db.start_classification_bulk([f[0] for f in files])
    print(files)
    for file_id, file_type in files:
        print(file_id, file_type)
        try:
            txt_path = os.path.join(EXTRACT_DIR, f"{file_id}_extracted.txt")
            print(txt_path)
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
            print(type(text))
            result, category = classify_file(text, file_type)
            print(file_id, result, category)
            if result == "done":
                db.done_classification(file_id, category)
            else:
                db.error_classification(file_id)
        except:
            print('error')
            db.error_classification(file_id)