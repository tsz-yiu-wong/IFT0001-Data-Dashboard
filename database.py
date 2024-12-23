import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的变量
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    "ssl_ca": os.getenv('DB_SSL_CA')
}

def connect_to_database(db_config=db_config):
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None


create_table_query = """
CREATE TABLE IF NOT EXISTS emissions_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255),
    sector VARCHAR(255),
    region VARCHAR(255),
    scope1_total VARCHAR(50),
    scope2_market_based VARCHAR(50),
    scope2_location_based VARCHAR(50)
)AUTO_INCREMENT = 1;
"""
def create_table(connection, create_table_query=create_table_query):
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully!")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()


insert_data_query = """
INSERT INTO emissions_data (
    company_name, sector, region, scope1_total, scope2_market_based, scope2_location_based
) VALUES (%s, %s, %s, %s, %s, %s);
"""
def insert_data(connection, insert_data_query=insert_data_query, data=[]):
    try:
        cursor = connection.cursor()
        for record in data:
            cursor.execute(insert_data_query, (
                record["company_name"],
                record["sector"],
                record["region"],
                record["scope1_total"],
                record["scope2_market_based"],
                record["scope2_location_based"]
            ))
            data.remove(record)
        connection.commit()
        print("Data inserted successfully!")
    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()


delete_query = """
DELETE FROM emissions_data
WHERE company_name = %s AND sector = %s AND region = %s;
"""
def delete_data(connection, delete_query=delete_query, delete_condition=()):
    try:
        cursor = connection.cursor()
        cursor.execute(delete_query, delete_condition)
        connection.commit()
        print(f"Successfully deleted {cursor.rowcount} rows!")
    except mysql.connector.Error as err:
        print(f"Error deleting data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()


def fetch_all_data(connection, select_query="SELECT * FROM emissions_data;"):
    try:
        cursor = connection.cursor()
        cursor.execute(select_query)
        results = cursor.fetchall()
        print("Table data:")
        for row in results:
            print(row)
    except mysql.connector.Error as err:
        print(f"Error fetching data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()


def close_connection(connection):
    try:
        if connection and connection.is_connected():
            connection.close()
            print("Database connection closed.")
    except mysql.connector.Error as err:
        print(f"Error closing connection: {err}")
