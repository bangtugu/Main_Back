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
    """아직 OCR 안된 파일 목록 (IS_EXTRACTED=0)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT FILE_ID FROM FILES WHERE IS_EXTRACTED = 0")
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def update_extracted_text(file_id: int):
    """OCR 완료된 파일 상태 갱신"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE FILES
        SET IS_EXTRACTED_PADDLEOCR = 1
        WHERE FILE_ID = :id
    """, {"id": file_id})
    conn.commit()
    cur.close()
    conn.close()
