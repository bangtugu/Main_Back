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

def create_tables_and_sequences():
    conn = get_connection()
    cursor = conn.cursor()

    # ---------------- 기존 테이블 및 시퀀스 삭제 ----------------
    drop_statements = [
        "DROP TABLE FOLDERS_CATEGORY",
        "DROP TABLE FOLDERS",
        "DROP TABLE FILES",
        "DROP TABLE LOGS",
        "DROP TABLE USERS",
        "DROP SEQUENCE SEQ_USER_ID",
        "DROP SEQUENCE SEQ_FOLDER_ID",
        "DROP SEQUENCE SEQ_FILE_ID",
        "DROP SEQUENCE SEQ_LOG_ID"
    ]
    for stmt in drop_statements:
        cursor.execute(f"BEGIN EXECUTE IMMEDIATE '{stmt}'; EXCEPTION WHEN OTHERS THEN NULL; END;")

    try:
        # ---------------- USERS ----------------
        cursor.execute("""
        CREATE TABLE USERS (
            USER_ID NUMBER PRIMARY KEY,
            USER_LOGIN_ID VARCHAR2(50) UNIQUE NOT NULL,
            USER_PASSWORD VARCHAR2(200) NOT NULL,
            EMAIL VARCHAR2(100) UNIQUE NOT NULL,
            ACCESS_KEY VARCHAR2(100),
            LAST_WORK DATE DEFAULT SYSDATE,
            CREATED_AT DATE DEFAULT SYSDATE
        )
        """)
        cursor.execute("CREATE SEQUENCE SEQ_USER_ID START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE")

        # ---------------- FOLDERS ----------------
        cursor.execute("""
        CREATE TABLE FOLDERS (
            FOLDER_ID NUMBER PRIMARY KEY,
            USER_ID NUMBER NOT NULL,
            FOLDER_NAME VARCHAR2(200),
            CATEGORY_LIST VARCHAR2(500),
            CONNECTED_DIRECTORY VARCHAR2(300),
            CLASSIFICATION_AFTER_CHANGE NUMBER(1) DEFAULT 1,
            LAST_WORK DATE DEFAULT SYSDATE,
            CONSTRAINT FK_FOLDERS_USER FOREIGN KEY (USER_ID)
                REFERENCES USERS(USER_ID)
                ON DELETE CASCADE
        )
        """)
        cursor.execute("CREATE SEQUENCE SEQ_FOLDER_ID START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE")

        # ---------------- FILES ----------------
        cursor.execute("""
        CREATE TABLE FILES (
            FILE_ID NUMBER PRIMARY KEY,
            USER_ID NUMBER NOT NULL,
            FOLDER_ID NUMBER,
            FILE_NAME VARCHAR2(200),
            FILE_TYPE VARCHAR2(50),
            FILE_PATH VARCHAR2(300),
            IS_TRANSFORM NUMBER(1) DEFAULT 0,
            TRANSFORM_TXT_PATH VARCHAR2(300),
            IS_CLASSIFICATION NUMBER(1) DEFAULT 0,
            CATEGORY VARCHAR2(200),
            UPLOADED_AT DATE DEFAULT SYSDATE,
            CONSTRAINT FK_FILES_USER FOREIGN KEY (USER_ID)
                REFERENCES USERS(USER_ID)
                ON DELETE CASCADE,
            CONSTRAINT FK_FILES_FOLDER FOREIGN KEY (FOLDER_ID)
                REFERENCES FOLDERS(FOLDER_ID)
                ON DELETE SET NULL
        )
        """)
        
        # ---------------- LOGS ----------------
        cursor.execute("""
        CREATE TABLE LOGS (
            LOG_ID NUMBER PRIMARY KEY,
            USER_ID NUMBER,
            LOG_TIME DATE DEFAULT SYSDATE,
            LOG_CONTENT VARCHAR2(1000),
            CONSTRAINT FK_LOGS_USER FOREIGN KEY (USER_ID)
                REFERENCES USERS(USER_ID)
                ON DELETE SET NULL
        )
        """)
        cursor.execute("CREATE SEQUENCE SEQ_LOG_ID START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE")

        # ---------------- FOLDERS_CATEGORY (리팩터링 버전) ----------------
        cursor.execute("""
        CREATE TABLE FOLDERS_CATEGORY (
            FOLDER_ID NUMBER NOT NULL,
            CATEGORY_NAME VARCHAR2(200) NOT NULL,
            CONSTRAINT PK_FOLDER_CATEGORY PRIMARY KEY (FOLDER_ID, CATEGORY_NAME),
            CONSTRAINT FK_FOLDER_CATEGORY FOREIGN KEY (FOLDER_ID)
                REFERENCES FOLDERS(FOLDER_ID)
                ON DELETE CASCADE
        )
        """)

        conn.commit()
        print("[INFO] All tables and sequences created successfully.")

        # ---------------- 샘플 데이터 삽입 ----------------
        cursor.execute("""
        INSERT INTO USERS (USER_ID, USER_LOGIN_ID, USER_PASSWORD, EMAIL)
        VALUES (SEQ_USER_ID.NEXTVAL, 'testuser', 'hashedpassword', 'test@example.com')
        """)
        cursor.execute("""
        INSERT INTO FOLDERS (FOLDER_ID, USER_ID, FOLDER_NAME)
        VALUES (SEQ_FOLDER_ID.NEXTVAL, 1, 'Default Folder')
        """)
        cursor.execute("""
        INSERT INTO FOLDERS_CATEGORY (FOLDER_ID, CATEGORY_NAME)
        VALUES (1, '회의록')
        """)
        cursor.execute("""
        INSERT INTO FOLDERS_CATEGORY (FOLDER_ID, CATEGORY_NAME)
        VALUES (1, '보고서')
        """)
        cursor.execute("""
        INSERT INTO FOLDERS_CATEGORY (FOLDER_ID, CATEGORY_NAME)
        VALUES (1, '수불대장')
        """)
        conn.commit()
        print("[INFO] Sample USER and FOLDER inserted.")

    except Exception as e:
        print(f"[ERROR] Failed to create tables/sequences: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_tables_and_sequences()
