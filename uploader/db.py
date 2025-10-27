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


def get_user_folders_with_details(user_id: int):
    """
    유저 ID에 해당하는 모든 폴더 정보 + 각 폴더의 파일 개수 + 카테고리 리스트
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            f.FOLDER_ID,
            f.USER_ID,
            f.FOLDER_NAME,
            f.CATEGORY_LIST,
            f.CONNECTED_DIRECTORY,
            f.CLASSIFICATION_AFTER_CHANGE,
            f.LAST_WORK,
            NVL(COUNT(DISTINCT fi.FILE_ID), 0) AS FILE_COUNT,
            LISTAGG(fc.CATEGORY_NAME, ',') WITHIN GROUP (ORDER BY fc.CATEGORY_NAME) AS CATEGORY_NAMES
        FROM FOLDERS f
        LEFT JOIN FILES fi 
            ON f.FOLDER_ID = fi.FOLDER_ID
        LEFT JOIN FOLDERS_CATEGORY fc
            ON f.FOLDER_ID = fc.FOLDER_ID
        WHERE f.USER_ID = :user_id
        GROUP BY 
            f.FOLDER_ID,
            f.USER_ID,
            f.FOLDER_NAME,
            f.CATEGORY_LIST,
            f.CONNECTED_DIRECTORY,
            f.CLASSIFICATION_AFTER_CHANGE,
            f.LAST_WORK
        ORDER BY f.LAST_WORK DESC
    """

    cursor.execute(query, {"user_id": user_id})
    columns = [col[0].lower() for col in cursor.description]
    rows = cursor.fetchall()

    results = []
    for row in rows:
        record = dict(zip(columns, row))
        # CATEGORY_NAMES를 리스트 형태로 변환
        if record.get("category_names"):
            record["category_names"] = record["category_names"].split(",")
        else:
            record["category_names"] = []
        results.append(record)

    cursor.close()
    conn.close()
    return results


def get_files_in_folder(folder_id: int):
    """
    특정 폴더 ID에 포함된 파일들의 상세 정보를 조회
    (오라클 11g 호환)
    """
    conn = oracledb.connect(user="YOUR_USER", password="YOUR_PW", dsn="YOUR_DSN")
    cursor = conn.cursor()

    query = """
        SELECT
            f.FILE_ID,
            f.FILE_NAME,
            f.FILE_TYPE,
            f.FILE_PATH,
            f.IS_TRANSFORM,
            f.IS_CLASSIFICATION,
            f.CATEGORY,
            f.UPLOADED_AT,
            NVL(u.USER_LOGIN_ID, 'unknown') AS USER_LOGIN_ID
        FROM FILES f
        LEFT JOIN USERS u ON f.USER_ID = u.USER_ID
        WHERE f.FOLDER_ID = :folder_id
        ORDER BY f.UPLOADED_AT DESC
    """

    cursor.execute(query, {"folder_id": folder_id})
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

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


def update_folder_categories(folder_id: int, categories: list[str]):
    conn = get_connection()
    cursor = conn.cursor()

    # 기존 카테고리 삭제
    cursor.execute("DELETE FROM FOLDERS_CATEGORY WHERE FOLDER_ID = :fid", {"fid": folder_id})

    # 새 카테고리 추가
    for cname in categories:
        cursor.execute("""
            INSERT INTO FOLDERS_CATEGORY (FOLDER_ID, CATEGORY_NAME)
            VALUES (:fid, :cname)
        """, {"fid": folder_id, "cname": cname})

    # FOLDERS 테이블의 CATEGORY_LIST 갱신
    cursor.execute("""
        UPDATE FOLDERS 
        SET LAST_WORK = SYSDATE
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