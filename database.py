import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    "ssl_ca": os.getenv('DB_SSL_CA')
}


# Database connection pool
connection_pool = None

# Initialize database connection pool
def init_connection_pool():
    global connection_pool
    if connection_pool is None:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            **db_config
        )
        print("Database connection pool initialized")

# Close database connection pool
def close_connection_pool():
    global connection_pool
    if connection_pool:
        while not connection_pool._cnx_queue.empty():
            conn = connection_pool._cnx_queue.get_nowait()
            if conn.is_connected():
                conn.close()
        connection_pool = None
        print("Database connection pool closed")


# Get database connection
def get_connection():
    if connection_pool is None:
        init_connection_pool()
    return connection_pool.get_connection()

# Get data from database
def get_data(query):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

# Get all data from database
def get_all_data(table_name):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


# Create table
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

# Insert data into database
def insert_data(insert_data_query, data):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(insert_data_query, data)
        connection.commit()
    finally:
        cursor.close()
        connection.close()


# Delete data from database
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

# Delete table
def delete_table(table_name):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        connection.commit()
    finally:
        cursor.close()
        connection.close()


# Print table data
def print_data(table_name):
    data = get_all_data(table_name)
    if not data:
        print("Table is empty")
        return
    
    # Get all column names
    columns = data[0].keys()
    
    # Print table header
    print("\n" + "="*100)
    print("\t".join(columns))
    print("-"*100)
    
    # Print data rows
    for row in data[:20]:
        print("\t".join(str(row[col]) if row[col] is not None else 'None' for col in columns))
    print("="*100 + "\n")


if __name__ == "__main__":

    init_connection_pool()

    try:
        # Test database functions
        print("\n=== Database functions test ===")
        test_table = "web_test"
        print(f"\n{test_table} content:")
        print_data(test_table)

    except Exception as e:
        print(f"Error occurred during testing: {e}")

    finally:
        # Close connection pool
        close_connection_pool()
        print("\nTest completed")