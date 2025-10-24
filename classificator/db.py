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


def get_unclassified_files():
    """
    IS_TRASCORM이 2이면서 IS_CLASSIFICATION이 0, 1인 파일 조회
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT FILE_ID, FILE_TYPE, IS_CLASSIFICATION FROM FILES WHERE IS_TRANSFORM = 2 and IS_CLASSIFICATION < 2 ORDER BY FILE_ID"
    )
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    return files


def start_classification_bulk(file_ids: list[int]):
    """
    여러 FILE_ID를 한 번에 IS_CLASSIFICATION = 1로 변경
    """
    if not file_ids:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.executemany(
        "UPDATE FILES SET IS_CLASSIFICATION = 1 WHERE FILE_ID = :fid",
        [{"fid": fid} for fid in file_ids]
    )

    conn.commit()
    cursor.close()
    conn.close()


def done_classification(file_id, result):
    """
    분류 완료 후 IS_CLASSIFICATION 컬럼 및 결과 업데이트
    file: {"file_id": int, "result": str}
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE FILES
        SET IS_CLASSIFICATION = 2,
            CLASSIFICATION_RESULT = :result
        WHERE FILE_ID = :fid
        """,
        {"fid": file_id, "result": result}
    )
    conn.commit()
    cursor.close()
    conn.close()


def error_classification(file_id):
    return