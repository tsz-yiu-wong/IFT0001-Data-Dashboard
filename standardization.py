import os
import re
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv

#################################################
#                 Find  ISIN                    #
#             (未完成，太特喵傻逼了)              #
#################################################
def find_ISIN(company_name):
    # Input: campnay name
    # Output: ISIN, sector, region, country in natural language

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')

    prompt = f"Find the ISIN of \"{company_name}\". \n \
          (If there is \"HK\" in the given name, find the ISIN for the Class H shares.) \n \
          Only answer me the ISIN, no explanation need. "
    #ps：tmd有的公司有两个ISIN真的太他妈傻逼了，搞了我一下午，操
    #ps2: tmd同样的prompt，chatgpt官网跟api返回的结果不一致，因为api不能访问外部链接，又搞了我一天，操

    # Call the OpenAI ChatGPT API to find the company's details
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system","content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    '''
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
    '''

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    return answer


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
        return {
            "scope1_direct": "null",
            "scope2_indirect": "null",
            "scope2_market_based": "null",
            "scope2_location_based": "null"
        }

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
            if 'scope 1' in page_text.lower(): # Use lower() for case-insensitive matching
                text += page_text
    
    if text == "" or len(text) <= 200:
        print(f"Error in extract text from {file_path}, the length of text is too small:{len(text)}.")
        return None

    return text

def find_data_in_text(company_name, pdf_text):
    # Input: emission related text
    # Output: emission data in natural language

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')

    prompt = f"According to the given content, find the latest scope 1 and scope 2 emissions data of \"{company_name}\". \n \
                Give me the data in the one of following pattern: \n \
                Pattern 1: \n \
                Scope 1 (direct): 111; unit. \n \
                Scope 2 (indirect): 222; unit. \n \
                Pattern 2: \n \
                Scope 1 (direct): 111; unit. \n \
                Scope 2 (martket-based): 333; unit. \n \
                Scope 2 (location-based): 444; unit. \n \
                If the data is missing, give the part as \"N/A\". \n \
                No explanation need. \n \
                -------------------------------------------- \n \
                {pdf_text}."

    # Call the OpenAI ChatGPT API to analyze the content and find emission data
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system","content": "You are a professional analyst who can identify emissions-related data from a company's sustainability report."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    return answer

def data_formatting(data_in_text):
    # Input: data in string form
    # Output: data in dictonary form
    # Sample 1:
    #   input: Scope 1 (direct): 65.50; ton CO2e. Scope 2 (indirect): 1,046.17; ton CO2e.
    #   output: {"scope1_direct":"65.50", "scope2_indirect":"1046.17", "scope2_market_based":"N/A", "scope2_location_based":"N/A"}
    # Sample 2:
    #   input: Scope 1 (direct): 59; MT CO2e. Scope 2 (market-based): 10,854; MT CO2e. Scope 2 (location-based): 20,614; MT CO2e.
    #   output: {"scope1_direct":"59", "scope2_indirect":"N/A", "scope2_market_based":"10854", "scope2_location_based":"20614"}
    
    # Helper function to handle error if no data found, without returning None or throwing an exception
    def safe_search(pattern, text, default="null"):
        match = re.search(pattern, text)
        return match.group(1).replace(",", "").strip() if match else default
    
    # Helper function to convert unit to MT
    def convert_unit(value_and_unit):
        if value_and_unit != "N/A":
            value, unit = value_and_unit.split(";")
            if "kg" in unit.strip().lower() or "kilogram" in unit.strip().lower():
                value = float(value) / 1000  # Convert to MT
                value = str(value)
            return value
        return "N/A"

    # If the statistical mode of scope2 is indirect
    if "indirect" in data_in_text:
        scope1_direct = re.search(r"Scope 1 \(direct\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
        scope1_direct_value = convert_unit(scope1_direct)
        scope2_indirect = re.search(r"Scope 2 \(indirect\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
        scope2_indirect_value = convert_unit(scope2_indirect)
        scope2_market_based_value = "N/A"
        scope2_location_based_value = "N/A"

    # If the statistical mode of scope2 is market based and location based
    elif "market" in data_in_text and "location" in data_in_text:
        scope1_direct = re.search(r"Scope 1 \(direct\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
        scope1_direct_value = convert_unit(scope1_direct)
        scope2_market_based = re.search(r"Scope 2 \(market-based\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
        scope2_market_based_value = convert_unit(scope2_market_based)
        scope2_location_based = re.search(r"Scope 2 \(location-based\):\s*([^\n]+)", data_in_text).group(1).replace(",", "").strip()
        scope2_location_based_value = convert_unit(scope2_location_based)
        scope2_indirect_value = "N/A"
    
    else:
        scope1_direct_value = scope2_indirect_value = scope2_market_based_value = scope2_location_based_value = "null"

    # If all data are "N/A", means the previous steps have something wrong. Mark as "null".
    if (scope1_direct_value == 'N/A' and scope2_indirect_value == 'N/A') or \
       (scope1_direct_value == 'N/A' and scope2_market_based_value == 'N/A' and scope2_location_based_value == 'N/A' ):
       scope1_direct_value = scope2_indirect_value = scope2_market_based_value = scope2_location_based_value = "null"

    # Construct data
    return {
        "scope1_direct": scope1_direct_value,
        "scope2_indirect": scope2_indirect_value,
        "scope2_market_based": scope2_market_based_value,
        "scope2_location_based": scope2_location_based_value
    }


# Test
if __name__ == "__main__":

    company_name = "MICROSOFT CORP"
    file_path = f"./reports/{company_name}.pdf"
    print(f"Start Processing {company_name}...")

    isin = find_ISIN(company_name)
    print(f"\n----------isin for {company_name}---------- \n {isin}")

    company_details = find_company_details(company_name)
    print(f"\n----------details for {company_name}---------- \n {company_details}")
    
    pdf_text = extract_text_from_pdf(file_path)
    print("\n----------pdf text----------\n", pdf_text[:100])

    data_in_text = find_data_in_text(company_name,pdf_text)
    print("\n----------data in text----------\n", data_in_text)

    emissions_data = data_formatting(data_in_text)
    print("\n----------emissions deta----------\n", emissions_data)