import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"

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

def mark_text_classified(db_id, category):
    """
    DB에 분류 결과 저장
    실제 구현 시 DB 업데이트 로직으로 교체
    """
    print(f"[DB] Record {db_id} marked as {category}")

def process_text_list(record_list):
    """
    DB에서 받은 미분류 텍스트 목록 순회하며 분류
    """
    while record_list:
        record = record_list.pop()  # LIFO
        db_id = record["id"]
        text = record["text"]

        category = classify_text(text)
        if category:
            mark_text_classified(db_id, category)
            print(f"[CLASSIFIED] {db_id} -> {category}")
        else:
            print(f"[SKIP] {db_id} classification failed")
