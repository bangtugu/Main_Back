import db_connect

conn = db_connect.get_connection()
cursor = conn.cursor()

# FILES 테이블 생성
cursor.execute("""
CREATE TABLE FILES (
    FILE_ID NUMBER PRIMARY KEY,
    TITLE VARCHAR2(255) NOT NULL,
    IS_EXTRACTED_PYTESSERACT NUMBER(1) DEFAULT 0,
    IS_EXTRACTED_EASYOCR NUMBER(1) DEFAULT 0,
    IS_EXTRACTED_PADDLEOCR NUMBER(1) DEFAULT 0,
    CONTENT VARCHAR2(2000)
    KEYWORDS VARCHAR2(500)
)
""")

conn.commit()
cursor.close()
conn.close()

print("✅ FILES 테이블이 OCRHUB 스키마에 생성되었습니다.")
