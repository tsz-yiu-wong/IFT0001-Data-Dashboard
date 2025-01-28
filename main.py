import os
import glob
import csv

from crawler import *
from process_pdf import *
import database as db

'''
def web_test(table_name, company_list_file,):
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


def create_table(table_name, file_path):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_name VARCHAR(50),
        ticker VARCHAR(30),
        isin VARCHAR(30) UNIQUE,
        weight DECIMAL(8, 6),
        sector VARCHAR(30),
        area VARCHAR(30),
        country_region VARCHAR(30),
        is_fiscal_year BOOLEAN DEFAULT NULL,
        scope1_direct VARCHAR(10) DEFAULT NULL,
        scope2_location VARCHAR(10) DEFAULT NULL,
        scope2_market VARCHAR(10) DEFAULT NULL,
        scope1_and_2 VARCHAR(10) DEFAULT NULL
    )AUTO_INCREMENT = 1;
    """
    db.create_table(create_table_query)

    
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过CSV表头
        for row in reader:
            name = row[0]
            ticker = row[1]
            isin = row[2]
            weight = row[3]
            sector = row[4]
            area = row[5]
            country_region = row[6]

            insert_data_query = f"INSERT INTO {table_name} (company_name, ticker, isin, weight, sector, area, country_region) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            db.insert_data(insert_data_query, (name, ticker, isin, weight, sector, area, country_region))


def create_table_data_only(table_name, file_path):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_name VARCHAR(50),
        isin VARCHAR(30) UNIQUE,
        scope1_direct VARCHAR(10),
        scope2_location VARCHAR(10),
        scope2_market VARCHAR(10)
    )AUTO_INCREMENT = 1;
    """
    db.create_table(create_table_query)

    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过CSV表头
        for row in reader:
            name = row[0]
            isin = row[2]
            scope1_direct = row[7]
            scope2_location = row[8]
            scope2_market = row[9]

            insert_data_query = f"INSERT INTO {table_name} (company_name, isin, scope1_direct, scope2_location, scope2_market) VALUES (%s, %s, %s, %s, %s)"
            db.insert_data(insert_data_query, (name, isin, scope1_direct, scope2_location, scope2_market))


def fill_emissions_data(table_name):
    
    # Get the whole company list
    get_data_query = f"SELECT company_name FROM {table_name}"
    company_names = db.get_data(get_data_query)

    # Handle each company
    for row in company_names:
        company_name = row['company_name']
        files_path = glob.glob(os.path.join("./reports", f"*{company_name}*"))
        file_path = files_path[0] if files_path else None

        if file_path == None:
            print(f"There is no report for {company_name}")
            continue
        
        scope1_direct, scope2_location, scope2_market, scope1_and_2 = find_emissions_data(company_name, file_path)

        insert_data_query = f"""
            INSERT INTO  {table_name} (
                company_name, scope1_direct, scope2_location, scope2_market, scope1_and_2
            ) VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                scope1_direct = VALUES(scope1_direct),
                scope2_location = VALUES(scope2_location),
                scope2_market = VALUES(scope2_market),
                scope1_and_2 = VALUES(scope1_and_2);
            """
        db.insert_data(insert_data_query, (company_name, scope1_direct, scope2_location, scope2_market, scope1_and_2))



if __name__ == "__main__":

    data_path = "./data/data.csv"

    db.delete_table("emissions_data")
    db.delete_table("bloomberg_emissions_data")
    create_table("emissions_data", data_path)
    create_table_data_only("bloomberg_emissions_data", data_path)

    #fill_emissions_data("emissions_data")

    db.print_data("emissions_data")

