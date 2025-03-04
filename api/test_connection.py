import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=REVENT1\\REVENTION;"
    "DATABASE=master;"  # Replace 'master' with the actual database name
    "UID=HRdb1_readonly;"
    "PWD=revention;"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
