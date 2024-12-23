import os
import re
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv

def extract_text_from_pdf(file_path):

    #Extract text from a PDF file.
    #param file_path: Path to the PDF file.
    #return: Extracted text as a string, or None if an error occurs.

    try:
        text = ""
        # Open the PDF file in binary read mode
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                # Always include the first page (we need to konw the campany name)
                if i == 0:
                    text += page_text
                # For other pages, include only if 'scope 1' is found
                elif 'scope 1' in page_text.lower():  # Use lower() for case-insensitive matching
                    text += page_text

    except Exception as e:
        print(f"Error while extracting text: {e}")
        return None

    return text

def find_data_in_text_pdf(pdf_text):

    #Use OpenAI API to analyze text and find emission data.
    #param pdf_text: The text extracted from the PDF file.
    #return: Extracted emission data as a string.
    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API'),
    prompt = f"According to the given content, find the scope 1 and scope 2 emission data. \n \
          Give me the data with following pattern: \n \
          Company name: Microsoft. \n \
          Sector: Internet. \n \
          Region: USA. \n \
          Scope 1 (total): 123; unit. \n \
          Scope 2 (martket-based): 456; unit. \n \
          Scope 2 (location-based): 789; unit. \n \
          If no related data, give the part as \"Null\". \n \
          If there are other ways to categorize, change the content in brackets. However, the two major categories of scope1 and scope2 must be maintained. \n \
          No need any other explanation word.  \n \
          --------------------- \n \
          {pdf_text}."

    # Call the OpenAI ChatGPT API to analyze the content
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


def extract_data(input_text):
    def safe_search(pattern, text, default="null"):
        match = re.search(pattern, text)
        return match.group(1).replace(",", "").strip().lower() if match else default

    # 使用安全提取方法
    company_name = safe_search(r"Company name:\s*(.+?)\.", input_text)
    sector = safe_search(r"Sector:\s*(.+?)\.", input_text)
    region = safe_search(r"Region:\s*(.+?)\.", input_text)
    scope1_total = safe_search(r"Scope 1 \(total\):\s*([\d,]+|Null);", input_text)
    scope2_market_based = safe_search(r"Scope 2 \(market-based\):\s*([\d,]+|Null);", input_text)
    scope2_location_based = safe_search(r"Scope 2 \(location-based\):\s*([\d,]+|Null);", input_text)

    # 构造数据
    return {
        "company_name": company_name,
        "sector": sector,
        "region": region,
        "scope1_total": scope1_total,
        "scope2_market_based": scope2_market_based,
        "scope2_location_based": scope2_location_based
    }



# Test Sample
if __name__ == "__main__":
    file_path = "./Kinross-Gold-2023-Sustainabillity-Report-Final.pdf"
    pdf_text = extract_text_from_pdf(file_path)
    print("----------pdf_text----------\n ", pdf_text[:100])
    emission_detail = find_data_in_text_pdf(pdf_text)
    print("----------emission_detail----------\n ", emission_detail)
    emission_data = extract_data(emission_detail)
    print("----------emission_data----------\n ", emission_data)
