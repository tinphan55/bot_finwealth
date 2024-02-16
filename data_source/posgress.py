import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import os

DATABASES_LIST = [
    {
        'host': '103.176.23.51',
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': os.getenv('DB_PORT'),
        }
]
database_config = DATABASES_LIST[0]


def connect():
    """ Connect to the PostgreSQL database server """
    database = database_config
    db_connection = None
    try:
        db_connection = psycopg2.connect(
            host= database['host'],
            port=database['port'],
            database =database['database'],
            user=database['user'],
            password=database['password'])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    finally:
        if db_connection is not None:
            #print('Database connect successfully.')
            return db_connection
        else:
            #print("Database connect error")
            exit()

def query_data(query):
    db_connection = connect()
    cur = db_connection.cursor()
    cur.execute(query)
    try:
        data = cur.fetchall()
        db_connection.commit()
    except psycopg2.ProgrammingError:
        print("No results found.")
        data = []  # Trả về danh sách rỗng nếu không có kết quả
    return data

def execute_query(query, data=None):
    db_connection = connect()
    cur = db_connection.cursor()
    try:
        if data is None:
            cur.execute(query)
        else:
            cur.execute(query, data)
        db_connection.commit()
        print("Query executed successfully.")
    except Exception as e:
        db_connection.rollback()
        print("Error executing query:", e)
    finally:
        cur.close()
        db_connection.close()


def engine ():
    database = database_config
    host = database['host']
    port = database['port']
    database_name = database['database']
    user = database['user']
    password = quote_plus(database['password'])
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database_name}')
    return engine

def read_sql_to_df(query):
    # Kết nối tới cơ sở dữ liệu PostgreSQL
    db_connection = engine ()
    # Tạo kết nối
    conn = db_connection.connect()
    # Chuyển đối tượng truy vấn sang dạng text
    query_text = text(query)
    # Thực hiện truy vấn để lấy dữ liệu từ cơ sở dữ liệu
    df = pd.read_sql(query_text, conn)
    # Đóng kết nối
    conn.close()
    return df

