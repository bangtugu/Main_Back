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


def get_file_name(file_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT TITLE FROM FILES WHERE FILE_ID = :file_id",
        {"file_id": file_id}
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def insert_file_record(file_id, original_name):
    """
    file_id: main.py, utils.py에서 관리하는 current_file_index
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO FILES (FILE_ID, TITLE) VALUES (:file_id, :title)",
        {"file_id": file_id, "title": original_name}
    )
    conn.commit()
    cursor.close()
    conn.close()
    return file_id


def get_all_files():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FILES ORDER BY FILE_ID DESC")
    rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def get_file_page(page, limit, search=None):
    conn = get_connection()
    cur = conn.cursor()

    min_row = (page - 1) * limit
    max_row = page * limit

    # WHERE 절 및 바인드 변수 설정
    where_clause = ""
    params = {"min_row": min_row, "max_row": max_row}

    if search:
        where_clause = "WHERE LOWER(TITLE) LIKE :title_kw OR LOWER(KEYWORDS) LIKE :keywords_kw"
        params["title_kw"] = f"%{search.lower()}%"
        params["keywords_kw"] = f"%{search.lower()}%"

    # 전체 개수
    if search:
        count_query = "SELECT COUNT(*) FROM FILES WHERE LOWER(TITLE) LIKE :title_kw OR LOWER(KEYWORDS) LIKE :keywords_kw"
        count_params = {"title_kw": params["title_kw"], "keywords_kw": params["keywords_kw"]}
    else:
        count_query = "SELECT COUNT(*) FROM FILES"
        count_params = {}

    cur.execute(count_query, count_params)
    total_count = cur.fetchone()[0]

    # 페이지네이션 쿼리
    if search:
        final_query = f"""
            SELECT * FROM (
                SELECT a.*, ROWNUM rnum
                FROM (
                    SELECT FILE_ID, TITLE,
                           IS_EXTRACTED_PYTESSERACT,
                           IS_EXTRACTED_EASYOCR,
                           IS_EXTRACTED_PADDLEOCR,
                           CONTENT,
                           KEYWORDS
                    FROM FILES
                    WHERE LOWER(TITLE) LIKE :title_kw OR LOWER(KEYWORDS) LIKE :keywords_kw
                    ORDER BY FILE_ID DESC
                ) a
                WHERE ROWNUM <= :max_row
            )
            WHERE rnum > :min_row
        """
        exec_params = {
            "title_kw": params["title_kw"],
            "keywords_kw": params["keywords_kw"],
            "min_row": min_row,
            "max_row": max_row
        }
    else:
        final_query = f"""
            SELECT * FROM (
                SELECT a.*, ROWNUM rnum
                FROM (
                    SELECT FILE_ID, TITLE,
                           IS_EXTRACTED_PYTESSERACT,
                           IS_EXTRACTED_EASYOCR,
                           IS_EXTRACTED_PADDLEOCR,
                           CONTENT,
                           KEYWORDS
                    FROM FILES
                    ORDER BY FILE_ID DESC
                ) a
                WHERE ROWNUM <= :max_row
            )
            WHERE rnum > :min_row
        """
        exec_params = {"min_row": min_row, "max_row": max_row}

    cur.execute(final_query, exec_params)
    columns = [col[0].lower() for col in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return {
        "files": rows,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "search": search
    }






def get_files_by_keyword(keyword):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FILES LIKE %:keyword%",
                {"keyword": keyword})
    rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows