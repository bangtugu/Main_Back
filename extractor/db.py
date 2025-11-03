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


def get_processing_file():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT FILE_ID FROM FILES WHERE IS_TRANSFORM = 1 ORDER BY FILE_ID"
    )
    file_set = set([f[0] for f in cursor.fetchall()])
    cursor.close()
    conn.close()
    return file_set


def get_unprocessed_files():
    """
    IS_TRANSFORM이 0, 1인 파일 조회
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT FILE_ID, FILE_TYPE, IS_TRANSFORM FROM FILES WHERE IS_TRANSFORM < 2 ORDER BY FILE_ID"
    )
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return files


def start_extract_bulk(file_ids: list[int]):
    if not file_ids:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE FILES SET IS_TRANSFORM = 1 WHERE FILE_ID = :fid",
        [{"fid": fid} for fid in file_ids]
    )
    conn.commit()
    cursor.close()
    conn.close()


def done_extract(file_id):
    """
    OCR 완료 후 IS_TRANSFORM 컬럼 업데이트
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE FILES SET IS_TRANSFORM = 2 WHERE FILE_ID = :file_id",
        {"file_id": file_id}
    )
    conn.commit()
    cursor.close()
    conn.close()


def unsupported_file_check(file_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE FILES SET IS_TRANSFORM = 3 WHERE FILE_ID = :file_id",
        {"file_id": file_id}
    )
    conn.commit()
    cursor.close()
    conn.close()