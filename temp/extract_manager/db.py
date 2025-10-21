import oracledb

oracledb.init_oracle_client(
    lib_dir=r"C:\Users\Bangtugu\Desktop\oracle\instantclient-basic-windows.x64-19.28.0.0.0dbru\instantclient_19_28"
)


def get_connection():
    return oracledb.connect(
        user="OCRHUB",
        password="ocrhub123",
        dsn="localhost:1521/xe"
    )


def get_unprocessed_files():
    """
    아직 추출 안된 파일 목록 조회
    - IS_EXTRACTED_PYTESSERACT, IS_EXTRACTED_EASYOCR, IS_EXTRACTED_PADDLEOCR 중 하나라도 0인 파일
    반환: [(FILE_ID, IS_EXTRACTED_PYTESSERACT, IS_EXTRACTED_EASYOCR, IS_EXTRACTED_PADDLEOCR), ...]
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT FILE_ID, IS_EXTRACTED_PYTESSERACT, IS_EXTRACTED_EASYOCR, IS_EXTRACTED_PADDLEOCR
        FROM FILES
        WHERE IS_EXTRACTED_PYTESSERACT = 0
           OR IS_EXTRACTED_EASYOCR = 0
           OR IS_EXTRACTED_PADDLEOCR = 0
    """)
    
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return rows
