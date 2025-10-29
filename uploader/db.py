import oracledb
import datetime

oracledb.init_oracle_client(
    lib_dir=r"C:\Users\Bangtugu\Desktop\oracle\instantclient-basic-windows.x64-19.28.0.0.0dbru\instantclient_19_28"
)

def get_connection():
    return oracledb.connect(
        user="OCRHUB",
        password="ocrhub123",
        dsn="localhost:1521/xe"
    )


def get_max_file_id():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(FILE_ID) FROM FILES")
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result


def insert_file_record(file_id, original_name, ftype, user_id, folder_id):
    """
    file_id: main.py, utils.py에서 관리하는 current_file_index
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO FILES (FILE_ID, USER_ID, FILE_NAME, FILE_TYPE, FOLDER_ID) VALUES (:file_id, :user_id, :title, :ftype, :folder_id)",
        {"file_id": file_id, "title": original_name, "ftype": ftype, "user_id": user_id, "folder_id": folder_id}
    )
    cursor.execute(
        """
        UPDATE FOLDERS
        SET FILE_CNT = NVL(FILE_CNT, 0) + 1,
            LAST_WORK = SYSDATE
        WHERE FOLDER_ID = :folder_id
        """,
        {"folder_id": folder_id}
    )
    conn.commit()
    cursor.close()
    conn.close()
    return


def get_user_files(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT FILE_ID, FILE_NAME, FILE_TYPE, IS_TRANSFORM, IS_CLASSFICATION, CLASSFICATION_RESULT FROM FILES WHERE USER_ID = :user_id",
        {"user_id": user_id}
    )
    files = [{'FILE_ID': f[0],
              'FILE_NAME': f[1],
              'FILE_TYPE': f[2],
              'IS_TRANSFORM': f[3],
              'IS_CLASSFICATION': f[4],
              'CLASSFICATION_RESULT': f[5]
              } for f in cursor.fetchall()]
    conn.commit()
    cursor.close()
    conn.close()
    return files


def get_user_folders(user_id: int):
    """
    특정 유저의 모든 폴더 정보를 가져옴.
    - 각 폴더의 파일 개수 포함
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            f.FOLDER_ID,
            f.FOLDER_NAME,
            f.CONNECTED_DIRECTORY,
            f.CLASSIFICATION_AFTER_CHANGE,
            f.FILE_CNT
        FROM FOLDERS f
        WHERE f.USER_ID = :user_id
        ORDER BY f.LAST_WORK DESC
    """

    cursor.execute(query, {"user_id": user_id})
    columns = [col[0].lower() for col in cursor.description]
    rows = cursor.fetchall()

    results = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()
    return results


def get_categories_in_folder(folder_id: int):
    """
    특정 폴더 ID에 포함된 카테고리 조회
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CATEGORY_NAME
        FROM FOLDERS_CATEGORY
        WHERE FOLDER_ID = :folder_id
        ORDER BY CATEGORY_NAME
    """, {"folder_id": folder_id})

    categories = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return categories


def get_files_in_folder(folder_id: int):
    """
    특정 폴더 ID에 포함된 파일들의 상세 정보를 조회
    (오라클 11g 호환)
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            f.FILE_ID,
            f.FILE_NAME,
            f.FILE_TYPE,
            f.FILE_PATH,
            f.IS_TRANSFORM,
            f.TRANSFORM_TXT_PATH,
            f.IS_CLASSIFICATION,
            f.CATEGORY,
            f.UPLOADED_AT
        FROM FILES f
        WHERE f.FOLDER_ID = :folder_id
        ORDER BY f.UPLOADED_AT DESC
    """

    cursor.execute(query, {"folder_id": folder_id})
    columns = [col[0] for col in cursor.description]
    results = []
    for row in cursor.fetchall():
        record = dict(zip(columns, row))
        # datetime을 ISO 문자열로 변환
        if isinstance(record.get("UPLOADED_AT"), (datetime.datetime, datetime.date)):
            record["UPLOADED_AT"] = record["UPLOADED_AT"].isoformat()
        results.append(record)

    cursor.close()
    conn.close()
    return results


def create_folder(user_id: int, folder_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
            INSERT INTO FOLDERS (FOLDER_ID, USER_ID, FOLDER_NAME, LAST_WORK)
            VALUES (SEQ_FOLDER_ID.NEXTVAL, :user_id, :folder_name, SYSDATE)
        """, {"user_id": user_id, "folder_name": folder_name})

    conn.commit()

    cursor.close()
    conn.close()
    return 


def rename_folder(folder_id: int, new_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE FOLDERS 
        SET FOLDER_NAME = :new_name, LAST_WORK = SYSDATE
        WHERE FOLDER_ID = :folder_id
    """, {"new_name": new_name, "folder_id": folder_id})

    rowcount = cursor.rowcount
    conn.commit()

    cursor.close()
    conn.close()
    return rowcount > 0


def create_folder_category(folder_id: int, category: str):
    conn = get_connection()
    cursor = conn.cursor()

    # 카테고리 추가
    cursor.execute("""
        INSERT INTO FOLDERS_CATEGORY (FOLDER_ID, CATEGORY_NAME)
        VALUES (:fid, :category)
    """, {"fid": folder_id, "category": category})

    # FOLDERS 테이블 업데이트
    cursor.execute("""
        UPDATE FOLDERS 
        SET LAST_WORK = SYSDATE,
            CLASSIFICATION_AFTER_CHANGE = 0
        WHERE FOLDER_ID = :fid
    """, {"fid": folder_id})

    conn.commit()
    cursor.close()
    conn.close()


def delete_folder_category(folder_id: int, category: str):
    conn = get_connection()
    cursor = conn.cursor()

    # 카테고리 삭제
    cursor.execute("""
        DELETE FROM FOLDERS_CATEGORY
        WHERE FOLDER_ID = :fid AND CATEGORY_NAME = :category
    """, {"fid": folder_id, "category": category})

    # FOLDERS 테이블 업데이트
    cursor.execute("""
        UPDATE FOLDERS 
        SET LAST_WORK = SYSDATE,
            CLASSIFICATION_AFTER_CHANGE = 0
        WHERE FOLDER_ID = :fid
    """, {"fid": folder_id})

    conn.commit()
    cursor.close()
    conn.close()


def delete_folder(folder_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM FOLDERS WHERE FOLDER_ID = :fid",
            {"fid": folder_id}
        )
        conn.commit()
        print(f"[INFO] Folder {folder_id} deleted successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to delete folder: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def user_last_work(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE FOLDERS 
        SET LAST_WORK = SYSDATE
        WHERE FOLDER_ID = :user_id
    """, {"user_id": user_id})

    conn.commit()
    cursor.close()
    conn.close()