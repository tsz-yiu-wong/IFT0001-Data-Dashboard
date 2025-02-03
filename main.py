import os
import glob
import csv

from crawler import *
from process_pdf import *
import database as db

# A test function to test creating a table
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
        next(reader)  # Skip CSV header
        for row in reader:
            company_name,isin,sector,region,country,scope1_direct,scope2_indirect,scope2_market_based,scope2_location_based = row

            insert_data_query = f"INSERT INTO {table_name} (company_name,isin,sector,region,country,scope1_direct,scope2_indirect,scope2_market_based,scope2_location_based) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            db.insert_data(insert_data_query, (company_name,isin,sector,region,country,scope1_direct,scope2_indirect,scope2_market_based,scope2_location_based))


# Create table with all company information and emissions data
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
        scope1_direct VARCHAR(20) DEFAULT NULL,
        scope2_location VARCHAR(20) DEFAULT NULL,
        scope2_market VARCHAR(20) DEFAULT NULL,
        scope1_and_2 VARCHAR(20) DEFAULT NULL
    )AUTO_INCREMENT = 1;
    """
    db.create_table(create_table_query)

    
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            name = row[0]
            ticker = row[1]
            isin = row[2]
            weight = row[3]
            sector = row[4]
            area = row[5]
            country_region = row[6]

            insert_data_query = f"INSERT INTO {table_name} \
                (company_name, ticker, isin, weight, sector, area, country_region) \
                VALUES (%s, %s, %s, %s, %s, %s, %s)"
            db.insert_data(insert_data_query, (name, ticker, isin, weight, sector, area, country_region))


# Create table with only emissions data
def create_table_bloomberg_data(table_name, file_path):
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
        scope1_direct VARCHAR(20),
        scope2_location VARCHAR(20),
        scope2_market VARCHAR(20)
    )AUTO_INCREMENT = 1;
    """
    db.create_table(create_table_query)

    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader) 
        for row in reader:
            name = row[0]
            ticker = row[1]
            isin = row[2]
            weight = row[3]
            sector = row[4]
            area = row[5]
            country_region = row[6]
            scope1_direct = row[7]
            scope2_location = row[9]
            scope2_market = row[8]

            insert_data_query = f"INSERT INTO {table_name} \
                (company_name, ticker, isin, weight, sector, area, country_region, \
                scope1_direct, scope2_location, scope2_market) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            db.insert_data(insert_data_query, (name, ticker, isin, weight, sector, area, country_region, scope1_direct, scope2_location, scope2_market))


# Fill emissions data into database
def fill_emissions_data(table_name, log_file_path, csv_file_path):
    
    # Get the whole company list
    get_data_query = f"SELECT * FROM {table_name}"
    results = db.get_data(get_data_query)
    for result in results:

        if result['scope1_direct'] != None or result['scope2_location'] != None \
            or result['scope2_market'] != None or result['scope1_and_2'] != None:
            continue

        company_name = result['company_name']
        isin = result['isin']

        result = find_emissions_data(company_name, log_file_path, csv_file_path) or (None, None, None, None, None)
        is_fiscal_year, scope1_direct, scope2_location, scope2_market, scope1_and_2 = result

        insert_data_query = f"""
            INSERT INTO  {table_name} (
                company_name, isin, is_fiscal_year, scope1_direct, scope2_location, scope2_market, scope1_and_2
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                is_fiscal_year = VALUES(is_fiscal_year),
                scope1_direct = VALUES(scope1_direct),
                scope2_location = VALUES(scope2_location),
                scope2_market = VALUES(scope2_market),
                scope1_and_2 = VALUES(scope1_and_2);
            """
        db.insert_data(insert_data_query, (company_name, isin, is_fiscal_year, scope1_direct, scope2_location, scope2_market, scope1_and_2))




if __name__ == "__main__":

    data_path = "./data/data.csv"
    number = 0
    while os.path.exists(f"./logs/process_pdf_log_{number}.txt"):
        number += 1
    log_file_path = f"./logs/process_pdf_log_{number}.txt"
    csv_file_path = f"./logs/process_pdf_excel_{number}.csv"

    #db.delete_table("emissions_data")
    #db.delete_table("bloomberg_emissions_data")
    create_table("emissions_data", data_path)
    create_table_bloomberg_data("bloomberg_emissions_data", data_path)

    fill_emissions_data("emissions_data", log_file_path, csv_file_path)
    db.print_data("emissions_data")
    db.print_data("bloomberg_emissions_data")