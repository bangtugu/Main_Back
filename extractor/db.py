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
    TXTTITLE이 NULL인 파일 조회
    반환: [(FILE_ID, TITLE, CTITLE)]
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT FILE_ID, TITLE, CTITLE FROM FILES WHERE TXTTITLE IS NULL ORDER BY FILE_ID"
    )
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return files

def update_txttitle(file_id, txt_filename):
    """
    OCR 완료 후 TXTTITLE 컬럼 업데이트
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE FILES SET TXTTITLE = :txttitle WHERE FILE_ID = :fid",
        {"txttitle": txt_filename, "fid": file_id}
    )
    conn.commit()
    cursor.close()
    conn.close()
