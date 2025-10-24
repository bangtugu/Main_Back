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


def insert_file_record(file_id, original_name, ftype, user_id):
    """
    file_id: main.py, utils.py에서 관리하는 current_file_index
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO FILES (FILE_ID, USER_ID, FILE_NAME, FILE_TYPE) VALUES (:file_id, :user_id, :title, :ftype)",
        {"file_id": file_id, "title": original_name, "ftype": ftype, "user_id": user_id}
    )
    conn.commit()
    cursor.close()
    conn.close()
    return file_id


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