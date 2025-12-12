import pyodbc

def get_connection(
    server="172.20.0.254",
    database="sel2_master",
    username="cltte",
    password="Cltte@#u2",
    driver="{ODBC Driver 17 for SQL Server}"
):
    try:
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
            f"KeepAlive=1;"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print("SQL ERROR:", e)
        return None
