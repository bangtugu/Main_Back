import oracledb

# ✅ 오라클 Instant Client 초기화
oracledb.init_oracle_client(
    lib_dir=r"C:\Users\Bangtugu\Desktop\oracle\instantclient-basic-windows.x64-19.28.0.0.0dbru\instantclient_19_28"
)

# ✅ DB 연결 함수
def get_connection():
    return oracledb.connect(
        user="OCRHUB",
        password="ocrhub123",
        dsn="localhost:1521/xe"
    )

# ✅ 아직 텍스트 추출되지 않은 파일 목록 조회
def get_unprocessed_files():
    """
    아직 요약되지 않은 파일 목록 조회
    - IS_EXTRACTED_EASYOCR = 1
    - CONTENT IS NULL
    반환: [FILE_ID, ...]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT FILE_ID
        FROM FILES
        WHERE IS_EXTRACTED_EASYOCR = 1
          AND CONTENT IS NULL
    """)
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def update_briefed_text(file_id: int, content: str, keywords: str):
    """
    Briefer에서 요약 완료 후 DB 갱신
    - content: 요약 텍스트
    - keywords: 콤마로 연결된 키워드 문자열
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # 만약 KEYWORDS 컬럼이 존재하지 않는 경우, ALTER TABLE로 추가 필요
    # 예: ALTER TABLE FILES ADD KEYWORDS VARCHAR2(500);
    
    cur.execute("""
        UPDATE FILES
        SET CONTENT = :content,
            KEYWORDS = :keywords
        WHERE FILE_ID = :file_id
    """, {"file_id": file_id, "content": content, "keywords": keywords})
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"🗂️ [{file_id}] DB에 CONTENT 및 KEYWORDS 갱신 완료")
