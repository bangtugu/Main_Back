import oracledb

# Oracle Instant Client 경로 지정
oracledb.init_oracle_client(
    lib_dir=r"C:\Users\Bangtugu\Desktop\oracle\instantclient-basic-windows.x64-19.28.0.0.0dbru\instantclient_19_28"
)

def get_connection():
    return oracledb.connect(
        user="OCRHUB",        # 유저 아이디
        password="ocrhub123", # 유저 비밀번호
        dsn="localhost:1521/xe"
    )

try:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # FILES 테이블 삭제 시도
        cursor.execute("DROP TABLE FILES")
        conn.commit()
        print("✅ FILES 테이블이 삭제되었습니다.")
    except oracledb.DatabaseError:
        # 테이블이 없을 경우 무시
        print("⚠️ FILES 테이블이 존재하지 않습니다.")

except oracledb.DatabaseError as e:
    error, = e.args
    print(f"❌ 데이터베이스 연결 또는 쿼리 오류: {error.message}")

finally:
    try:
        cursor.close()
        conn.close()
    except Exception:
        pass
