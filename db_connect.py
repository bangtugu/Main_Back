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