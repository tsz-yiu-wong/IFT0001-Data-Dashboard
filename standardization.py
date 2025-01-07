import os
import re
import requests
import json
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv
'''
#################################################
#                 Find  ISIN                    #
#                  (待优化)                      #
#################################################
def find_ISIN(company_name):
    # Input: campnay name
    # Output: ISIN, sector, region, country in natural language

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')

    prompt = f"Find the ISIN of \"{company_name}\". \n \
          (If there is \"HK\" in the given name, find the ISIN for the Class H shares.) \n \
          Only answer me the ISIN, no explanation need. "
    #ps：tmd有的公司有两个ISIN真的太傻逼了，搞了我一下午，艹
    #ps2: tmd同样的prompt，chatgpt官网跟api返回的结果不一致，因为api不能访问外部链接，又搞了我一天，艹

    # Call the OpenAI ChatGPT API to find the company's details
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system","content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API'))
    response = client.chat.completions.create(
        model="o1-mini",
        messages=[
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )
    

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    return answer

def find_ISIN_with_openfigi(company_name):
    url = "https://api.openfigi.com/v3/mapping"
    load_dotenv()
    api_key = os.getenv('OPENFIGI_API')
    headers = {
        'Content-Type': 'application/json',
        'X-OPENFIGI-APIKEY': api_key
    }   
    data = [{"idType": "TICKER", "idValue": "APPLE"}]
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(data)
        for item in data:
            isin = item.get("data", [{}])[0].get("idIsin", "No ISIN found")
            print(f"Company: {company_name}, ISIN: {isin}")
    else:
        print(f"Error: {response.status_code}, {response.text}")
'''

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
def find_emissions_data(company_name, file_path):
    
    pdf_text =extract_text_from_pdf(file_path)
    if pdf_text == None:
        return ("null", "null", "null")

    data_in_text = find_data_in_text(company_name, pdf_text)
    emissions_data = data_formatting(data_in_text)

    return emissions_data

def extract_text_from_pdf(file_path):
    # Input: pdf file
    # Output: extracted emission related text
    text = ""
    with open(file_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            # Only need the pages if 'scope 1' keyword is found
            if 'scope 1' in page_text.lower() or 'scope 2' in page_text.lower(): # Use lower() for case-insensitive matching
                text += page_text

    return text

def find_data_in_text(company_name, pdf_text):
    # Input: emission related text
    # Output: emission data in natural language

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')

    prompt = f"According to the given text, find the latest scope 1 and scope 2 emissions data of \"{company_name}\",  \
                and then give me the data in the following summary pattern: \n \
                Scope 1 (direct): 111 unit. \n \
                Scope 2 (location-based): 222 unit. \n \
                Scope 2 (martket-based): 333 unit. \n \
                --------------------------------- \n \
                1. You need to pay attention to the unit, if it is not found, use the default unit: tCO2e. \n \
                2. You also need to pay attention to whether scope2 is calculated based on Location-based or Market-based. \
                If no specific statistical method is found, it is assumed to be location-based. \n \
                3. If the data is missing, or you not sure about the data, leave the part as \"N/A\". \n \
                4. No explanation need. \n \
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

# Helper function to convert unit to MT
def convert_unit(value_and_unit):
    if value_and_unit != "N/A.":
        # 分割数值和单位,处理可能包含多个空格的情况
        parts = value_and_unit.split(";")[0].strip().split(" ", 1)
        value = float(parts[0])
        unit = parts[1].lower().strip()
        
        # 转换单位，默认单位是metric ton / MT / t / tonne
        if "short ton" in unit or ("ton" in unit and "metric" not in unit): 
            value = round(value * 0.90718, 2) 
        elif "long ton" in unit: 
            value = round(value * 1.01605, 2) 
        elif "kilogram" in unit or "kg" in unit:
            value = value / 1000
            if abs(value) < 1:
                # 找到第一个非零数字的位置
                str_num = f"{num:.10f}"
                first_nonzero = next(i for i, c in enumerate(str_num.replace("-", "").replace("0.", "")) if c != '0')
                value = round(num, first_nonzero + 3) # 如果是零点几，保留三位有效数
            else:
                value = round(value, 2) 
        
        if "kilo" in unit and "gram" not in unit:
            value = round(value * 1000, 2)
        elif "million" in unit:
            value = round(value * 1000000, 2)
            
        # 如果是整数则去掉小数点后的.0
        if value.is_integer():
            return str(int(value))
        return str(value)
    return "N/A"

def data_formatting(data_in_text):
    # Input: data in string form
    # Output: data in dictonary form

    scope1_direct = re.search(r"Scope 1 \(direct\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
    scope1_direct_value = convert_unit(scope1_direct)
    if scope1_direct_value == "N/A":
        return ("null", "null", "null")

    scope2_location_based = re.search(r"Scope 2 \(location-based\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
    scope2_location_based_value = convert_unit(scope2_location_based)
    scope2_market_based = re.search(r"Scope 2 \(market-based\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
    scope2_market_based_value = convert_unit(scope2_market_based)
    
    return (scope1_direct_value, scope2_location_based_value, scope2_market_based_value)


# Test
if __name__ == "__main__":
    
    company_name = "APPLE"
    file_path = f"./reports/{company_name}.pdf"
    print(f"\n==========Start Processing {company_name}==========")
    
    #isin = find_ISIN_with_openfigi(company_name)
    #print(f"\n-----isin for {company_name}----- \n {isin}")

    #company_details = find_company_details(company_name)
    #print(f"\n-----details for {company_name}----- \n {company_details}")
    
    pdf_text = extract_text_from_pdf(file_path)
    data_in_text = find_data_in_text(company_name,pdf_text)
    print("\n-----data in text-------\n", data_in_text)

    emissions_data = data_formatting(data_in_text)
    print("\n-----data in dict-------\n", emissions_data)
    '''

    # 获取reports目录下所有PDF文件
    reports_dir = "./reports"
    pdf_files = [f for f in os.listdir(reports_dir) if f.endswith('.pdf')]
    
    for pdf_file in pdf_files:
        # 从文件名获取公司名称
        company_name = os.path.splitext(pdf_file)[0]
        file_path = os.path.join(reports_dir, pdf_file)
        print(f"\n==========Start Processing {company_name}==========")
        pdf_text = extract_text_from_pdf(file_path)
        data_in_text = find_data_in_text(company_name, pdf_text)
        print("data in text:\n", data_in_text)

        emissions_data = data_formatting(data_in_text)
        print("data in dict:\n", emissions_data)
    '''