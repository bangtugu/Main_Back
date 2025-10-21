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

def fetch_unprocessed_files():
    """
    IS_TRANSFORM이 0인 파일 조회
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT FILE_ID FROM FILES WHERE IS_TRANSFORM = 0 ORDER BY FILE_ID"
    )
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return files

def update_is_transform(file_id):
    """
    OCR 완료 후 IS_TRANSFORM 컬럼 업데이트
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE FILES SET IS_TRANSFORM = 1 WHERE FILE_ID = :fid",
        {"fid": file_id}
    )
    conn.commit()
    cursor.close()
    conn.close()
