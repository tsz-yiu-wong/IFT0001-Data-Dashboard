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
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def close_connection(connection):
    try:
        if connection and connection.is_connected():
            connection.close()
    except mysql.connector.Error as err:
        print(f"Error closing connection: {err}")



###----------Public----------###
__all__ = ['connect_to_database','close_connection','create_table','insert_data','delete_data','delete_all_data','delete_table','get_data','get_all_data']

create_table_query = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(30) UNIQUE,
    index_weight DECIMAL(8, 6),
    isin VARCHAR(30) DEFAULT NULL,
    sector VARCHAR(30) DEFAULT NULL,
    region VARCHAR(30) DEFAULT NULL,
    country VARCHAR(30) DEFAULT NULL,
    scope1_direct VARCHAR(10) DEFAULT NULL,
    scope2_indirect VARCHAR(10) DEFAULT NULL,
    scope2_market_based VARCHAR(10) DEFAULT NULL,
    scope2_location_based VARCHAR(10) DEFAULT NULL
)AUTO_INCREMENT = 1;
"""
def create_table(table_name="emissions_data"):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        formatted_query = create_table_query.format(table_name=table_name)
        cursor.execute(formatted_query)
        connection.commit()
        print(f"Table '{table_name}' created successfully!")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)



def insert_data(insert_data_query, data):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute(insert_data_query, data)
        connection.commit()
        print(f"Data inserted successfully! Data: {data}")
    except mysql.connector.Error as err:
        print(f"Error inserting data {data}: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)





'''
insert_data_query = """
INSERT INTO {table_name} (
    company_name, isin, sector, region, country, scope1_total, scope2_market_based, scope2_location_based
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    sector = VALUES(sector),
    region = VALUES(region),
    country = VALUES(country),
    scope1_total = VALUES(scope1_total),
    scope2_market_based = VALUES(scope2_market_based),
    scope2_location_based = VALUES(scope2_location_based);
"""
def insert_data2(insert_data_query, data, table_name="emissions_data"):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        formatted_query = insert_data_query.format(table_name=table_name)
        for record in data:
            cursor.execute(formatted_query, (
                record["company_name"],
                record["isin"],
                record["sector"],
                record["region"],
                record["country"],
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
'''

delete_data_query = "DELETE FROM {table_name} WHERE company_name = %s;"
def delete_data(company_name, table_name="emissions_data"):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        formatted_query = delete_data_query.format(table_name=table_name)
        cursor.execute(formatted_query, (company_name,))
        connection.commit()
        print(f"Successfully deleted {cursor.rowcount} rows!")
    except mysql.connector.Error as err:
        print(f"Error deleting data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)

delete_all_data_query = "DELETE FROM {table_name};"
def delete_all_data(table_name="emissions_data"):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        formatted_query = delete_all_data_query.format(table_name=table_name)
        cursor.execute(formatted_query)
        connection.commit()
        print(f"Successfully deleted {cursor.rowcount} rows from the table!")
    except mysql.connector.Error as err:
        print(f"Error deleting data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)

delete_table_query = "DROP TABLE {table_name};"
def delete_table(table_name="emissions_data"):
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        formatted_query = delete_table_query.format(table_name=table_name)
        cursor.execute(formatted_query)
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

get_all_data_query = "SELECT * FROM {table_name};"
def get_all_data(table_name="emissions_data"):
    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        formatted_query = get_all_data_query.format(table_name=table_name)
        cursor.execute(formatted_query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error fetching data: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            close_connection(connection)