import time
from classifier.utils import process_text_list  # utils에서 분류 처리
from db_module import fetch_unclassified_texts  # DB에서 미분류 텍스트 LIFO로 가져오기

CHECK_INTERVAL = 5  # 초 단위

def main():
    print("Classifier started. Monitoring DB for unclassified texts...")
    while True:
        # DB에서 미분류 텍스트 목록 가져오기 (최신이 리스트 끝)
        unclassified = fetch_unclassified_texts()
        if not unclassified:
            print("No unclassified texts. Waiting...")
            time.sleep(CHECK_INTERVAL)
            continue

        # utils에 바로 전달
        process_text_list(unclassified)

if __name__ == "__main__":
    main()
