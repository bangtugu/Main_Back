import db_connect

# conn = db_connect.get_connection()
# cursor = conn.cursor()

# try:
#     # 1️⃣ 임시 테이블 생성 (원하는 컬럼 순서)
#     cursor.execute("""
#         ALTER TABLE FILES
#         ADD KEYWORDS VARCHAR2(500)
#     """)

#     conn.commit()
#     print("✅ FILES 테이블 컬럼 삽입.")

# except Exception as e:
#     print("❌ 오류 발생:", e)
#     conn.rollback()

# finally:
#     cursor.close()
#     conn.close()

# try:
#     # 1️⃣ 임시 테이블 생성 (원하는 컬럼 순서)
#     cursor.execute("""
#         CREATE TABLE FILES_TMP (
#             FILE_ID NUMBER PRIMARY KEY,
#             TITLE VARCHAR2(255) NOT NULL,
#             IS_EXTRACTED_PYTESSERACT NUMBER(1) DEFAULT 0,
#             IS_EXTRACTED_EASYOCR NUMBER(1) DEFAULT 0,
#             IS_EXTRACTED_PADDLEOCR NUMBER(1) DEFAULT 0,
#             CONTENT VARCHAR2(2000)
#         )
#     """)

#     # 2️⃣ 기존 데이터 복사 (IS_EXTRACTED → IS_EXTRACTED_EASYOCR)
#     cursor.execute("""
#         INSERT INTO FILES_TMP (FILE_ID, TITLE, IS_EXTRACTED_PYTESSERACT, IS_EXTRACTED_EASYOCR, IS_EXTRACTED_PADDLEOCR, CONTENT)
#         SELECT FILE_ID, TITLE, 0, IS_EXTRACTED, 0, CONTENT
#         FROM FILES
#     """)

#     # 3️⃣ 기존 테이블 삭제
#     cursor.execute("DROP TABLE FILES")

#     # 4️⃣ 임시 테이블 이름 변경
#     cursor.execute("ALTER TABLE FILES_TMP RENAME TO FILES")

#     conn.commit()
#     print("✅ FILES 테이블 컬럼 순서 및 구조가 목표 구조로 변경되었습니다.")

# except Exception as e:
#     print("❌ 오류 발생:", e)
#     conn.rollback()

# finally:
#     cursor.close()
#     conn.close()
