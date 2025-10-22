import requests
import db

OLLAMA_API_URL = "http://localhost:11434/api/generate"


async def classify_file(text, file_type):
    result = ''
    try:
        # 2️⃣ Gemma3 모델용 prompt 구성
        system_prompt = (
            "너는 문서의 형식을 분류하는 AI야."
            "사용자가 제공하는 텍스트를 보고 아래 중 가장 알맞은 하나의 문서 유형을 답해."
            "가능한 유형: 회의록, 일부개정법률안, 입법, 법률안, 기타."
            f"제공되는 텍스트의 원래 확장자는 {file_type}였어."
            "출력은 TEXT로 분류 딱 한 단어만 반환해"
            "\"카테고리명\""
        )
        end_prompt = (
            "지금까지의 내용을 바탕으로 아래의 문서 형식 중"
            "가장 알맞은 하나의 형식을 TEXT로 딱 한 단어만 반환해"
            "\"카테고리명\""
        )
        
        payload = {
            "model": "gemma3:1b",  # Modelfile로 만든 Gemma3 모델 이름
            "prompt": f"{system_prompt}\n{text}\n{end_prompt}",
            "max_tokens": 300,
            "stream": False
        }

        # 3️⃣ Ollama API 호출
        response = requests.post(OLLAMA_API_URL, json=payload)
        

        # chunks = response.text.strip().splitlines()

        # # response 필드 합치기
        # final_text = ""
        # for chunk in chunks:
        #     try:
        #         j = json.loads(chunk)
        #         final_text += j.get("response", "")
        #     except json.JSONDecodeError:
        #         pass

        # print(final_text)  # -> {"category": "법률안"}


        # response.raise_for_status()
        # print(1, response)
        
        # # 4️⃣ JSON 파싱
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
        # results[file.filename] = json.dumps(classification_json)

    except Exception as e:
        return "error", e

    return "done", result
    

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
    
    db.start_classfication_bulk(files)

    for file_id, file_type in files:
        try:
            text = open(file_id+"_extract.txt")
            result, category = classify_file(text, file_type)
            if result == "done":
                db.done_classfication(file_id, category)
            else:
                db.error_classfication(file_id)
        except:
            db.error_classfication(file_id)