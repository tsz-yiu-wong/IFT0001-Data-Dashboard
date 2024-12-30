import os
import mysql.connector
from dotenv import load_dotenv


###----------Private----------###
load_dotenv()
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
        print("Database connected.")
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def close_connection(connection):
    try:
        if connection and connection.is_connected():
            connection.close()
            print("Database connection closed.")
    except mysql.connector.Error as err:
        print(f"Error closing connection: {err}")



###----------Public----------###
#__all__ = ['connect_to_database','close_connection','create_table','insert_data','delete_data','get_all_data']
__all__ = ['create_table','insert_data','delete_data','delete_all_data','delete_table','get_data','get_all_data']

create_table_query = """
CREATE TABLE IF NOT EXISTS emissions_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) UNIQUE,
    sector VARCHAR(255),
    region VARCHAR(255),
    scope1_total VARCHAR(50),
    scope2_market_based VARCHAR(50),
    scope2_location_based VARCHAR(50)
)AUTO_INCREMENT = 1;
"""
def create_table(create_table_query=create_table_query):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully!")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)


insert_data_query = """
INSERT INTO emissions_data (
    company_name, sector, region, scope1_total, scope2_market_based, scope2_location_based
) VALUES (%s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    sector = VALUES(sector),
    region = VALUES(region),
    scope1_total = VALUES(scope1_total),
    scope2_market_based = VALUES(scope2_market_based),
    scope2_location_based = VALUES(scope2_location_based);
"""
def insert_data(data=[]):
    try:
        connection = connect_to_database()
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
        if connection:
            close_connection(connection)


delete_data_query = "DELETE FROM emissions_data WHERE company_name = %s;"
def delete_data(company_name):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute(delete_data_query, (company_name,))
        connection.commit()
        print(f"Successfully deleted {cursor.rowcount} rows!")
    except mysql.connector.Error as err:
        print(f"Error deleting data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)

delete_all_data_query = "DELETE FROM emissions_data;"
def delete_all_data():
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute(delete_all_data_query)
        connection.commit()
        print(f"Successfully deleted {cursor.rowcount} rows from the table!")
    except mysql.connector.Error as err:
        print(f"Error deleting data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)

delete_table_query = "DROP TABLE emissions_data;"
def delete_table():
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute(delete_table_query)
        connection.commit()
        print(f"Successfully deleted {cursor.rowcount} table!")
    except mysql.connector.Error as err:
        print(f"Error deleting table: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)

def get_data(get_data_query, params=None):
    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(get_data_query, params)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error fetching data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)


get_all_data_query = "SELECT * FROM emissions_data;"
def get_all_data():
    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(get_all_data_query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error fetching data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)