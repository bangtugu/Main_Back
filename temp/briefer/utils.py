import os
import db
import requests
import json

# Ollama API 정보
OLLAMA_URL = "http://localhost:11434/api/generate"  # 로컬 Ollama
MODEL = "gemma3:1b"
MAX_CHARS = 5000   # Gemma3 토큰 제한 고려 (입력 텍스트 자르기)
SUMMARY_MAX_LEN = 300  # 최종 요약 글자 수 제한

# 경로 설정
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted_texts/easyocr")
SUMMARY_DIR = os.path.join(BASE_DIR, "summary_texts")

# 디렉토리 없으면 생성
os.makedirs(SUMMARY_DIR, exist_ok=True)


def run_brief(file_id: int):
    """
    file_id 기반으로 TXT 파일 읽어서 Gemma3 요약 후 DB + TXT 저장
    """
    txt_path = os.path.join(EXTRACT_DIR, f"{file_id}.txt")
    if not os.path.exists(txt_path):
        print(f"❌ [{file_id}] TXT 파일 없음")
        return

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Ollama API 호출 프롬프트
        prompt = f"""
            아래 본문을 300자 이내로 3줄 요약하고, 핵심 키워드 3~4개를 뽑아.
            출력은 아래 JSON 형식 **그대로만**, **다른 말 없이** 작성해.

            출력 예시:
            {{
            "content": "요약내용 (100자 이내)",
            "keywords": ["키워드1", "키워드2", "키워드3"]
            }}

            본문:
            {text}
            """

        payload = {
            "model": MODEL,
            "prompt": prompt[:MAX_CHARS],
            "stream": False,
        }
        
        print('file_id = {} 요약 시작'.format(file_id))
        response = requests.post(OLLAMA_URL, json=payload, timeout=600)
        response.raise_for_status()
        data = response.json()

        # Ollama 응답 파싱
        brief_text = data.get("response", "").strip()
        try:
            parsed = json.loads(brief_text)
        except json.JSONDecodeError:
            # 일부 모델이 코드블록(````json ... ````)로 감싸는 경우 처리
            cleaned = (
                brief_text.replace("```json", "")
                .replace("```", "")
                .strip()
            )
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError:
                print(f"⚠️ [{file_id}] JSON 파싱 실패 → 내용 그대로 저장")
                db.update_briefed_text(file_id, brief_text, "")
                return

        content = parsed.get("content", "").strip()
        keywords = ", ".join(parsed.get("keywords", []))

        # ✅ DB 업데이트
        print(content[:50])
        print(keywords)
        db.update_briefed_text(file_id, content, keywords)

        # ✅ TXT 파일로 저장
        summary_path = os.path.join(SUMMARY_DIR, f"{file_id}_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ [{file_id}] 요약 완료 및 저장 → {summary_path}")

    except Exception as e:
        print(f"❌ [{file_id}] 요약 실패:", e)
