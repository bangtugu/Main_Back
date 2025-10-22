import oracledb

# Oracle Instant Client 경로 설정 (Windows 기준 예시)
oracledb.init_oracle_client(
    lib_dir=r"C:\Users\Bangtugu\Desktop\oracle\instantclient-basic-windows.x64-19.28.0.0.0dbru\instantclient_19_28"
)

def get_connection():
    return oracledb.connect(
        user="OCRHUB",
        password="ocrhub123",
        dsn="localhost:1521/xe"
    )

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # USERS 테이블
        cursor.execute("""
        CREATE TABLE USERS (
            USER_ID NUMBER PRIMARY KEY,
            USER_LOGIN_ID VARCHAR2(50) UNIQUE NOT NULL,
            EMAIL VARCHAR2(100) UNIQUE NOT NULL,
            PASSWORD_HASH VARCHAR2(200) NOT NULL,
            ACCESS_KEY VARCHAR2(100),
            USER_DIRECTORY VARCHAR2(200),
            CREATED_AT DATE DEFAULT SYSDATE
        )
        """)

        # USERS 시퀀스
        cursor.execute("""
        CREATE SEQUENCE SEQ_USER_ID
        START WITH 1
        INCREMENT BY 1
        NOCACHE
        NOCYCLE
        """)

        # FILES 테이블
        cursor.execute("""
        CREATE TABLE FILES (
            FILE_ID NUMBER PRIMARY KEY,
            USER_ID NUMBER NOT NULL,
            FILE_NAME VARCHAR2(200) NOT NULL,
            FILE_TYPE VARCHAR2(50),
            FILE_DIRECTORY VARCHAR2(300),
            IS_TRANSFORM NUMBER(1) DEFAULT 0,
            IS_CLASSIFICATION NUMBER(1) DEFAULT 0,
            HIDE NUMBER(1) DEFAULT 0,
            CLASSIFICATION_RESULT VARCHAR2(200),
            ERROR_MESSAGE VARCHAR2(400),
            UPLOADED_AT DATE DEFAULT SYSDATE,
            IS_SUMMARY NUMBER(1) DEFAULT 0,
            CONSTRAINT FK_FILES_USER FOREIGN KEY (USER_ID)
                REFERENCES USERS (USER_ID)
                ON DELETE CASCADE
        )
        """)

        conn.commit()
        print("[INFO] Tables and sequence created successfully.")

    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_tables()
