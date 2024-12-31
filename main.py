import os
import glob

from crawler import *
from standardization import *
from database import *

def initialize_database(company_list_file, table_name):

    create_table(table_name)

    with open(company_list_file, 'r', encoding='utf-8') as file:
        for line in file:
            company_name, remain = line.strip().split('\t', 1)
            index_weight = remain.split('%')[0].strip()

            insert_data_query = f"INSERT INTO {table_name} (company_name, index_weight) VALUES (%s, %s)"
            insert_data(insert_data_query, (company_name,index_weight))

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

def fill_isin(table_name):

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
        
        emissions_data = find_emissions_data(company_name, file_path)

        insert_data_query = f"""
            INSERT INTO  {table_name} (
                company_name, scope1_direct, scope2_indirect, scope2_market_based, scope2_location_based
            ) VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                scope1_direct = VALUES(scope1_direct),
                scope2_indirect = VALUES(scope2_indirect),
                scope2_market_based = VALUES(scope2_market_based),
                scope2_location_based = VALUES(scope2_location_based);
            """
        data = (company_name,
                emissions_data['scope1_direct'],
                emissions_data['scope2_indirect'],
                emissions_data['scope2_market_based'],
                emissions_data['scope2_location_based'])
        insert_data(insert_data_query, data)

    return


company_list_file = './test_list.txt'
reports_folder = './reports'

delete_all_data("emissions_data")
delete_table("emissions_data")
initialize_database(company_list_file, "emissions_data")

#fill_isin("emissions_data")
#fill_company_details("emissions_data")
fill_emissions_data("emissions_data", reports_folder)
