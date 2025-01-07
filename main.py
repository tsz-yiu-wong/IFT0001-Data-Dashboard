import os
import glob
import csv

from crawler import *
from standardization import *
from database import *


def web_test(company_list_file, table_name):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_name VARCHAR(50) UNIQUE,
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
    create_table(create_table_query)

    with open(company_list_file, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过CSV表头
        for row in reader:
            company_name,isin,sector,region,country,scope1_direct,scope2_indirect,scope2_market_based,scope2_location_based = row

            insert_data_query = f"INSERT INTO {table_name} (company_name,isin,sector,region,country,scope1_direct,scope2_indirect,scope2_market_based,scope2_location_based) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            insert_data(insert_data_query, (company_name,isin,sector,region,country,scope1_direct,scope2_indirect,scope2_market_based,scope2_location_based))



'''
def initialize_database2(company_list_file, table_name):
    create_table_query = f"""
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
    create_table(create_table_query)

    with open(company_list_file, 'r', encoding='utf-8') as file:
        for line in file:
            company_name, remain = line.strip().split('\t', 1)
            index_weight = remain.split('%')[0].strip()

            insert_data_query = f"INSERT INTO {table_name} (company_name, index_weight) VALUES (%s, %s)"
            insert_data(insert_data_query, (company_name,index_weight))
'''

'''
def fill_database(table_name):

    get_data_query = f"SELECT company_name FROM {table_name}"
    company_names = get_data(get_data_query)

    for row in company_names:
        company_name = row['company_name']
        isin = find_ISIN(company_name)
        company_details = find_company_details(company_name)
        
        files_path = glob.glob(os.path.join('./report', f"*{company_name}*"))
        #file_path = glob.glob(os.path.join('./report', f"*{company_name}*.pdf"))
        file_path = files_path[0] if files_path else None
        if file_path == None:
            print(f"There is no report for {company_name}")
            continue
        emissions_data = find_emissions_data(company_name, file_path)

        insert_data_query = f"""
            INSERT INTO  {table_name} (company_name, isin, sector, region, country, scope1_direct, scope2_indirect, scope2_market_based, scope2_location_based)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                isin = VALUES(isin),
                sector = VALUES(sector),
                region = VALUES(region),
                country = VALUES(country),
                scope1_direct = VALUES(scope1_direct),
                scope2_indirect = VALUES(scope2_indirect),
                scope2_market_based = VALUES(scope2_market_based),
                scope2_location_based = VALUES(scope2_location_based);
            """
        data = (company_name,
                isin,
                company_details['sector'],
                company_details['region'],
                company_details['country'],
                emissions_data['scope1_direct'],
                emissions_data['scope2_indirect'],
                emissions_data['scope2_market_based'],
                emissions_data['scope2_location_based'])

        insert_data(insert_data_query, data)

'''

def create_table(table_name):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_name VARCHAR(50) UNIQUE,
        isin VARCHAR(30) DEFAULT NULL,
        sector VARCHAR(30) DEFAULT NULL,
        region VARCHAR(30) DEFAULT NULL,
        country VARCHAR(30) DEFAULT NULL,
        scope1_direct VARCHAR(10) DEFAULT NULL,
        scope2_location_based VARCHAR(10) DEFAULT NULL,
        scope2_market_based VARCHAR(10) DEFAULT NULL
    )AUTO_INCREMENT = 1;
    """
    create_table(create_table_query)


def initialize_database(file_path, table_name):
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过CSV表头
        for row in reader:
            # 只读取需要的列
            name = row[1]  # Name在第2列
            isin = row[9]  # ISIN在第10列 
            sector = row[2]  # Sector在第3列

            insert_data_query = f"INSERT INTO {table_name} (company_name, isin, sector) VALUES (%s, %s, %s)"
            insert_data(insert_data_query, (name, isin, sector))

'''
def fill_isin_and_sector(table_name):
    not_found_in_db = 0  # CSV中没有匹配到的记录数
    not_found_in_csv = 0  # 数据库中没有匹配到的记录数

    csv_data = {}
    with open("isin_and_sector.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过CSV表头
        for row in reader:
            company_name, isin, sector = row
            csv_data[company_name] = (isin, sector)
    
    print(csv_data["APPLE INC"])

    # 查询数据库中是否存在匹配的company_name
    result = get_data(f"SELECT company_name FROM {table_name}")
    
    for company_name_dict in result:
        company_name = company_name_dict["company_name"]

        # 检查该company_name是否存在于CSV数据中
        if company_name in csv_data:
            isin, sector = csv_data[company_name]

            query = f"""
            INSERT INTO  {table_name} (company_name, isin, sector) VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                isin = VALUES(isin),
                sector = VALUES(sector);
            """
            insert_data(query, (company_name, isin, sector))
        else:
            # 如果没有找到匹配的name，增加计数
            not_found_in_csv += 1

    # 查询数据库中没有在CSV文件中匹配到的记录
    #db_names = get_data(f"SELECT company_name FROM {table_name}")

    # 查询CSV中没有在数据库匹配到的记录
    '''for name in csv_data:
        result = get_data(f"SELECT * FROM {table_name} WHERE company_name = %s", (name,))
        if not result:
            not_found_in_db += 1
    '''
    # 输出结果
    print(f"CSV中没有匹配到的记录数: {not_found_in_db}")
    print(f"MySQL中没有匹配到的记录数: {not_found_in_csv}")


def fill_isin2(table_name):

    get_data_query = f"SELECT company_name FROM {table_name}"
    company_names = get_data(get_data_query)

    for row in company_names:
        company_name = row['company_name']
        isin = find_ISIN(company_name)
        

        insert_data_query = f"""
            INSERT INTO  {table_name} (company_name, isin) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                isin = VALUES(isin);
            """
        insert_data(insert_data_query, (company_name, isin))
'''

def fill_company_details(table_name):

    get_data_query = f"SELECT company_name FROM {table_name}"
    company_names = get_data(get_data_query)

    for row in company_names:
        company_name = row['company_name']
            
        company_details = find_company_details(company_name)

        insert_data_query = f"""
            INSERT INTO  {table_name} (
                company_name, sector, region, country
            ) VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                sector = VALUES(sector),
                region = VALUES(region),
                country = VALUES(country);
            """
        data = (company_name,
                company_details['sector'],
                company_details['region'],
                company_details['country'])
        insert_data(insert_data_query, data)


def fill_emissions_data(table_name, reports_folder_path):
    
    get_data_query = f"SELECT company_name FROM {table_name}"
    company_names = get_data(get_data_query)

    for row in company_names:
        company_name = row['company_name']
        files_path = glob.glob(os.path.join('./reports', f"*{company_name}*"))
        #file_path = glob.glob(os.path.join('./report', f"*{company_name}*.pdf"))
        file_path = files_path[0] if files_path else None

        if file_path == None:
            print(f"There is no report for {company_name}")
            continue
        
        scope1_direct, scope2_location_based, scope2_market_based = find_emissions_data(company_name, file_path)

        insert_data_query = f"""
            INSERT INTO  {table_name} (
                company_name, scope1_direct, scope2_location_based, scope2_market_based
            ) VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                scope1_direct = VALUES(scope1_direct),
                scope2_location_based = VALUES(scope2_location_based),
                scope2_market_based = VALUES(scope2_market_based);
            """
        data = (company_name, scope1_direct, scope2_location_based, scope2_market_based)
        insert_data(insert_data_query, data)


def print_data(table_name):
    # Print data
    result = get_all_data(table_name)

    keys = result[0].keys()  # 获取第一个记录的所有键（字段名）
    header = "\t".join(keys)  # 将所有字段名用tab连接起来
    print(header)
    print("-" * len(header))  # 打印与标题等长的分隔线

    for record in result:
        print("\t".join(str(record[key]) for key in keys))  # 遍历记录并打印每一列

    print("-" * len(header))  # 打印结束的分隔线


company_list_file = './test_list_1410.txt'
csv_file = './isin_and_sector.csv'
reports_folder = './reports'

#delete_all_data("emissions_data_1410")
#delete_table("emissions_data_2336")
#initialize_database(csv_file, "emissions_data_2336")

#fill_isin_and_sector("emissions_data_1410")
#fill_company_details("emissions_data")
#fill_emissions_data("emissions_data", reports_folder)
#print_data("emissions_data_2336")

#web_test("./100_test_list.csv","web_test")
#print_data("web_test")