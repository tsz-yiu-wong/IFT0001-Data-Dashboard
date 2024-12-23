import requests
from bs4 import BeautifulSoup
import re
import os
import glob

# Function to search Google and return the first PDF URL
def search_csr_report(company_name):
    search_query = f"{company_name} CSR report"
    search_url = f"https://www.google.com/search?q={search_query}"
    print(search_url)
    print()

    response = requests.get(search_url)

    if response.status_code != 200:
        print("Failed to fetch Google search results.")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")
    print(links)

    # Extract and check PDF URLs
    for link in links:
        href = link.get("href")
        if href and "http" in href:
            url_match = re.search(r"url\?q=(https?://[\w./-]+)&", href)
            if url_match:
                pdf_url = url_match.group(1)
                if pdf_url.endswith(".pdf"):
                    print(pdf_url)
                    return pdf_url

    print("No PDF found in search results.")
    return None

# Function to download the PDF
def download_pdf(pdf_url, company_name):
    response = requests.get(pdf_url, stream=True)
    if response.status_code == 200:
        file_name = f"{company_name}_CSR_Report.pdf"
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"PDF downloaded successfully: {file_name}")
    else:
        print("Failed to download the PDF.")



# Test Sample
if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    pdf_url = search_csr_report(company_name)

    if pdf_url:
        print(f"PDF URL found: {pdf_url}")
        download_pdf(pdf_url, company_name)
    else:
        print("Could not find a PDF URL for the specified company.")