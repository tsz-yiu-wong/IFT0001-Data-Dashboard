import os
import re
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv

# Input: pdf file
# Output: extracted emission related text
# Return None if eroor occurs
def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                # Only need the first page (to konw the campany name) and the pages if 'scope 1' is found
                if i == 0:
                    text += page_text
                elif 'scope 1' in page_text.lower(): # Use lower() for case-insensitive matching
                    text += page_text
    
    except Exception as e:
        print(f"Error while extracting text: {e}")
        return None

    return text

# Input: emission related text
# Output: emission data in natural language
#-----------------------------------------------
# Sample output:
# Company name: KINROSS GOLD CORPORATION.
# Scope 1 (total): 1,017,651; tonnes CO2e.
# Scope 2 (location-based): 373,597; tonnes CO2e.
# Scope 2 (market-based): Null.
#------------------------------------------------
def find_data_in_text(pdf_text):

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')

    prompt = f"According to the given content, find the latest scope 1 and scope 2 emission data. \n \
          Give me the data in following pattern: \n \
          Company name: Microsoft. \n \
          Scope 1 (total): 123; unit. \n \
          Scope 2 (martket-based): 456; unit. \n \
          Scope 2 (location-based): 789; unit. \n \
          If no related data, give the part as \"Null\". \n \
          If there are other ways to categorize, change the content in brackets. However, the two major categories of scope1 and scope2 must be maintained. \n \
          No any explanation.  \n \
          -------------------------------------------- \n \
          {pdf_text}."

    # Call the OpenAI ChatGPT API to analyze the content and find emission data
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system","content": "You are a professional analyst who can identify emissions-related data from a company's sustainability report."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    return answer

# Input: campnay name
# Output: ISIN, sector, region, country in natural language
def find_company_details(company_name):

    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API')

    prompt = f"Find the ISIN, Category names of sectors, regions and countries in MSCI ACWI Index of \"{company_name}\". \n \
          Give me the answer in the following pattern: \n \
          Company name: Microsoft. (Name in MSCI ACWI Index) \n \
          ISIN: US1234567891. \n \
          Sector: Information Technology. \n \
          Region: North America. \n \
          Country: US. \n \
          No any explanation."

    # Call the OpenAI ChatGPT API to find the company's details
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system","content": "You are a professional financial analyst and are very familiar with ISIN and MSCI ACWI Index."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    # Extract the answer text from the response
    answer = response.choices[0].message.content.strip()
    return answer

# Input: data in string format, Output: data in dictonary format
def data_formatting(company_detail, emission_data):
    
    # Safe serach to handle error if no data found, without returning None or throwing an exception
    def safe_search(pattern, text, default="null"):
        match = re.search(pattern, text)
        return match.group(1).replace(",", "").strip() if match else default

    company_name = safe_search(r"Company name:\s*(.+?)\.", company_detail)
    company_name = company_name.title()
    isin = safe_search(r"ISIN:\s*(.+?)\.", company_detail)
    sector = safe_search(r"Sector:\s*(.+?)\.", company_detail)
    region = safe_search(r"Region:\s*(.+?)\.", company_detail)
    country = safe_search(r"Country:\s*(.+?)\.", company_detail)

    scope1_total = safe_search(r"Scope 1 \(total\):\s*([\d,]+|Null);", emission_data)
    scope2_market_based = safe_search(r"Scope 2 \(market-based\):\s*([\d,]+|Null);", emission_data)
    scope2_location_based = safe_search(r"Scope 2 \(location-based\):\s*([\d,]+|Null);", emission_data)

    # Construct data
    return {
        "company_name": company_name,
        "isin": isin,
        "sector": sector,
        "region": region,
        "country": country,
        "scope1_total": scope1_total,
        "scope2_market_based": scope2_market_based,
        "scope2_location_based": scope2_location_based
    }

def pdf_to_database(pdf_url):
    return

# Test
if __name__ == "__main__":
    file_path = "./reports/Zoom.pdf"
    pdf_text = extract_text_from_pdf(file_path)
    print("\n----------pdf text----------\n", pdf_text[:100])
    emission_detail = find_data_in_text(pdf_text)
    print("\n----------emission_deta----------\n", emission_detail)
    company_detail = find_company_details(pdf_text)
    print("\n----------company_details----------\n ", company_detail)
    all_details = data_formatting(company_detail, emission_detail)
    print("\n----------all_details----------\n ", all_details)