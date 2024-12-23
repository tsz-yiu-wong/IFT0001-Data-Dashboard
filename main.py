import os
import glob
from dotenv import load_dotenv

from crawler import *
from standardization import extract_text_from_pdf, find_data_in_text_pdf, extract_data
from database import connect_to_database, create_table, insert_data, fetch_all_data, delete_data, close_connection


directory_path = "./reports"
all_emission_data = []

# 获取目录下所有的 PDF 文件
pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))

for file_path in pdf_files:
    print(f"Processing file: {file_path}")
    try:
        pdf_text = extract_text_from_pdf(file_path)
        emission_detail = find_data_in_text_pdf(pdf_text)
        emission_data = extract_data(emission_detail)
        all_emission_data.append(emission_data)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


# 输出或保存处理结果
for data in all_emission_data:
    print(data)


load_dotenv()  # 加载 .env 文件中的变量
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    "ssl_ca": os.getenv('DB_SSL_CA')
}

connection = connect_to_database(db_config)
if connection is None:
    exit()
create_table(connection)
insert_data(connection, data=all_emission_data)
fetch_all_data(connection)
#delete_condition = ("Tesla", "Automotive", "Global")
#delete_data(connection, delete_condition=delete_condition)
#fetch_all_data(connection)
close_connection(connection)