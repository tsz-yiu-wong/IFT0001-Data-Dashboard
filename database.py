import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    "ssl_ca": os.getenv('DB_SSL_CA')
}

connection_pool = None

def init_connection_pool():
    global connection_pool
    if connection_pool is None:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            **db_config
        )
        print("Database connection pool initialized")

def close_connection_pool():
    global connection_pool
    if connection_pool:
        # 关闭连接池中的所有连接
        while not connection_pool._cnx_queue.empty():
            conn = connection_pool._cnx_queue.get_nowait()
            if conn.is_connected():
                conn.close()
        connection_pool = None
        print("Database connection pool closed")


def get_connection():
    if connection_pool is None:
        init_connection_pool()
    return connection_pool.get_connection()

def get_data(query):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

def get_all_data(table_name):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def create_table(create_table_query):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        connection.commit()
        print(f"Table created successfully!")
    finally:
        cursor.close()
        connection.close()

def insert_data(insert_data_query, data):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(insert_data_query, data)
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def delete_data(company_name, table_name):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = f"DELETE FROM {table_name} WHERE company_name = %s"
        cursor.execute(query, (company_name,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def print_table_data(table_name):
    """打印表格内容的辅助函数"""
    data = get_all_data(table_name)
    if not data:
        print("表格为空")
        return
    
    # 获取所有列名
    columns = data[0].keys()
    
    # 打印表头
    print("\n" + "="*100)
    print("\t".join(columns))
    print("-"*100)
    
    # 打印数据行
    for row in data:
        print("\t".join(str(row[col]) if row[col] is not None else 'None' for col in columns))
    print("="*100 + "\n")


if __name__ == "__main__":

    # 初始化连接池
    init_connection_pool()

    try:
        # 测试数据库功能
        print("\n=== 数据库功能测试 ===")

        # 1. 测试表格查询
        test_table = "web_test"  # 修改为要测试的表格名
        print(f"\n1. 查询表格 {test_table} 的内容：")
        print_table_data(test_table)

        '''
        # 2. 测试条件查询
        print("\n2. 测试条件查询（例：查询特定地区的公司）：")
        query = f"SELECT * FROM {test_table} WHERE region = 'asia' LIMIT 5"
        results = get_data(query)
        if results:
            print("\n条件查询结果：")
            print("\t".join(results[0].keys()))
            print("-"*100)
            for row in results:
                print("\t".join(str(val) if val is not None else 'None' for val in row.values()))
        else:
            print("没有找到匹配的数据")
        '''

    except Exception as e:
        print(f"测试过程中出现错误: {e}")

    finally:
        # 关闭连接池
        close_connection_pool()
        print("\n测试完成")