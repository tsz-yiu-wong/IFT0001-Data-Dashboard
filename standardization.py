import os
import re
import requests
import json
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv
from openai import OpenAI

#################################################
#       Find sector, region and country         #
#         （中国公司找不到 之后得手动填）          #
#################################################
def find_company_details(company_name):
    # Input: campnay name
    # Output: ISIN, sector, region, country in natural language

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')
    
    prompt = f"Find the sector, region and country of \"{company_name}\". \n \
          Give me the answer in the following pattern: \n \
          Sector: Communication Services. (Category names of sectors in MSCI ACWI Index)\n \
          Region: North America. (Category names of regions in MSCI ACWI Index)\n \
          Country: US. (Category names of countries in MSCI ACWI Index)\n \
          If you cannot find the related information, give it as \"null\" \n \
          End with full stop. No explanation need."
    
    # Call the OpenAI ChatGPT API to find the company's details
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system","content": "You are a professional financial analyst and are very familiar with MSCI ACWI Index."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    
    # Extract the keyword from the answer text  
    sector = re.search(r"Sector:\s*(.+?)\.", answer).group(1)
    region = re.search(r"Region:\s*(.+?)\.", answer).group(1)
    country = re.search(r"Country:\s*(.+?)\.", answer).group(1)

    return {
        "sector": sector,
        "region": region,
        "country": country,
    }


#################################################
#        Find emissions data from PDF           #
#################################################

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        
        # 如果PDF是加密的，尝试空密码解密
        if reader.is_encrypted:
            try:
                reader.decrypt('')  # 尝试空密码
            except:
                print(f"Error: Cannot decrypt PDF: {pdf_path}")
                return None
                
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if ('scope 1' in page_text.lower() or 'scope 2' in page_text.lower()) and \
                  ('2024' in page_text.lower() or '2023' in page_text.lower()):
                text += page_text
        return text
    
    except Exception as e:
        print(f"Error processing PDF: {pdf_path}")
        print(f"Error message: {str(e)}")
        with open('log2.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"Error | File: {pdf_path} | Error: {str(e)}\n")
        return None


def find_data_in_text_chatgpt(company_name, pdf_text):
    # Input: emission related text
    # Output: emission data in natural language

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')

    prompt = f"According to the given text, find the latest scope 1 and scope 2 emissions data of \"{company_name}\",  \
                and then give me the data in the one of following patterns: \n \
                ##Pattern 1: \n \
                Scope 1 (direct): 1,234 unit. \n \
                Scope 2 (location-based): 2,345 unit. \n \
                Scope 2 (martket-based): 3,456 unit. \n \
                ##Pattern 2: \n \
                Scope 1 and 2 (total): 1,234 unit. \n \
                ##Requirements: \n \
                1. Pay attention to the notes and comments about the accurately calculation method of Scope 2.\n \
                2. Pattern2 is used only the scope1 and scope2 are counted together. \n \
                3. Pay attention and try hard to find the unit of the data.\n \
                4. If the data is missing, or you not sure about the data, leave the part as \"N/A\". \n \
                5. No explanation need. \n \
                ---------------------------------- \n \
                {pdf_text}."

    # Call the OpenAI ChatGPT API to analyze the content and find emission data
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system","content": "You are a professional analyst who can find scope 1 and scope 2 emissions data from a company's sustainability report."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    return answer


def find_data_in_text_deepseek(company_name, pdf_text):

    load_dotenv()
    client = OpenAI(api_key=os.getenv('DEEPSEEK_API'), base_url="https://api.deepseek.com")

    prompt = f"According to the given text, find the latest scope 1 and scope 2 emissions data of \"{company_name}\",  \
                and then give me the data in the one of following patterns: \n \
                ##Pattern 1: \n \
                Scope 1 (direct): 1,234 unit. \n \
                Scope 2 (location-based): 2,345 unit. \n \
                Scope 2 (martket-based): 3,456 unit. \n \
                ##Pattern 2: \n \
                Scope 1 and 2 (total): 1,234 unit. \n \
                ##Requirements: \n \
                1. Pay attention to the notes and comments about the accurately calculation method of Scope 2.\n \
                2. Pattern2 is used only the scope1 and scope2 are counted together. \n \
                3. Pay attention and try hard to find the unit of the data.\n \
                4. If the data is missing, or you not sure about the data, leave the part as \"N/A\". \n \
                5. No explanation need. \n \
                ---------------------------------- \n \
                {pdf_text}."

    # Call the OpenAI ChatGPT API to analyze the content and find emission data
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a professional analyst who can find scope 1 and scope 2 emissions data from a company's sustainability report."},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    return answer

# Helper function to convert unit to MT
def convert_unit(value_and_unit):
    
    # 分割数值和单位,处理可能包含多个空格的情况
    parts = value_and_unit.split(";")[0].strip().split(" ", 1)
    try:
        value = float(parts[0])
        unit = parts[1].lower().strip()
        unit_capital = parts[1].strip()
    except:
        return "N/A"
    
    ### 转换单位，默认单位是metric ton / t / tonne ###
    # 短吨: short ton / ton
    if "short ton" in unit or ("ton" in unit and "metric" not in unit and "tonnes" not in unit): 
        value = round(value * 0.90718, 2) 
    # 长吨: long ton
    elif "long ton" in unit: 
        value = round(value * 1.01605, 2) 
    # 千克: kilogram / kg
    elif "kilogram" in unit or "kg" in unit:
        value = value / 1000
        if abs(value) < 1: # 如果是零点几，保留三位有效数
            # 找到第一个非零数字的位置
            str_num = f"{value:.10f}"
            first_nonzero = next(i for i, c in enumerate(str_num.replace("-", "").replace("0.", "")) if c != '0')
            value = round(value, first_nonzero + 3)
        else:
            value = round(value, 2) 
    # 千吨: thousand tonne / kt
    if "thousand" in unit or "kilo tonne" in unit or "kt" in unit:
        value = round(value * 1000, 2)
    # 百万吨: million tonne / Mt
    elif "million" in unit or "Mt" in unit_capital: # MT是Metric Tonne的缩写，但Mt是Million Tonne的缩写
        value = round(value * 1000000, 2)
    elif "billion" in unit or "gt" in unit:
        value = round(value * 1000000000, 2)
    
    # 如果是整数则去掉小数点后的.0
    if value.is_integer():
        return str(int(value))
    return str(value)

def data_formatting(data_in_text):
    # Input: data in string form
    # Output: data in dictonary form
    
    #if "total" in data_in_text:
    #    return ("null", "null", "null")

    # 安全搜索 scope 1
    scope1_match = re.search(r"Scope 1 \(direct\):\s*([^\n]+)", data_in_text)
    if not scope1_match:
        scope1_direct_value = "null"
    else:
        scope1_direct = scope1_match.group(1).replace(",", "").strip()
        scope1_direct_value = convert_unit(scope1_direct)

    # 安全搜索 scope 2 location-based
    scope2_location_match = re.search(r"Scope 2 \(location-based\):\s*([^\n]+)", data_in_text)
    if not scope2_location_match:
        scope2_location_based_value = "null"
    else:
        scope2_location_based = scope2_location_match.group(1).replace(",", "").strip()
        scope2_location_based_value = convert_unit(scope2_location_based)

    # 安全搜索 scope 2 market-based  
    scope2_market_match = re.search(r"Scope 2 \(market-based\):\s*([^\n]+)", data_in_text)
    if not scope2_market_match:
        scope2_market_based_value = "null"
    else:
        scope2_market_based = scope2_market_match.group(1).replace(",", "").strip()
        scope2_market_based_value = convert_unit(scope2_market_based)
    
    return (scope1_direct_value, scope2_location_based_value, scope2_market_based_value)


def find_emissions_data(company_name, file_path, log_file_path):

    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"\n=========={company_name}==========\n")

    pdf_text =extract_text_from_pdf(file_path)
    if pdf_text == None:
        return ("null", "null", "null")

    data_in_text = find_data_in_text_deepseek(company_name, pdf_text)
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"【data in sentance】\n{data_in_text}\n")

    emissions_data = data_formatting(data_in_text)
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"【data only】\n{emissions_data}\n")

    return emissions_data
    

if __name__ == "__main__":

    log_file_path = 'log5_deepseek.txt'
    '''
    # 单个公司测试
    company_name = "HEINEKEN HOLDING NV"
    file_path = f"./reports2/{company_name}.pdf"
    emissions_data = find_emissions_data(company_name, file_path, log_file_path)
    '''
    # 批量处理测试
    reports_dir = "./reports5"
    pdf_files = [f for f in os.listdir(reports_dir) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        company_name = os.path.splitext(pdf_file)[0]
        file_path = os.path.join(reports_dir, pdf_file)
        emissions_data = find_emissions_data(company_name, file_path, log_file_path)
            