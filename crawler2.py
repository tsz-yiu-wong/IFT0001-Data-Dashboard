import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import time
import urllib.parse
from standardization import extract_text_from_pdf, find_emissions_data
import urllib3
import os
from datetime import datetime

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def init_driver():
    """初始化 Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')
    return webdriver.Chrome(options=options)

def search_pdf_in_google(company_name, driver):
    """在Google中搜索公司的PDF报告"""
    search_query = f"{company_name} sustainability report 2023 pdf -responsibilityreports"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
    print(f"Searching pdf: {search_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    response = requests.get(search_url, headers=headers)
    response.encoding = 'utf-8'
    
    soup = BeautifulSoup(response.text, 'html.parser')
    search_results = soup.select('div.g')
    print(f"Found {len(search_results)} results.")
    
    if len(search_results) == 0:
        driver.get(search_url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        search_results = soup.select('div.g')
        print(f"Selenium found {len(search_results)} results.")
    
    # 检查PDF链接
    for result in search_results:
        link = result.find('a')
        if not link:
            continue
        url = link.get('href')
        if not url:
            continue
        if '.pdf' in url.lower():
            print(f"Found PDF: {url}")
            return url
    
    return None

def search_webpage_in_google(company_name, driver):
    """搜索公司的可持续发展页面"""
    search_query = f"{company_name} sustainability report -responsibilityreports"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
    print(f"Searching webpage: {search_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    search_results = soup.select('div.g')
    
    # 直接返回第一个搜索结果的链接
    if search_results:
        link = search_results[0].find('a')
        if link:
            url = link.get('href')
            if url:
                print(f"Found webpage: {url}")
                return url
    
    # 如果没有找到结果,使用selenium尝试
    driver.get(search_url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    search_results = soup.select('div.g')
    
    if search_results:
        link = search_results[0].find('a')
        if link:
            url = link.get('href')
            if url:
                print(f"Found webpage: {url}")
                return url
    
    return None

def find_pdf_in_webpage(url, driver):
    """在网页中查找PDF下载链接"""
    driver.get(url)
    time.sleep(3)
    
    links = driver.find_elements(By.TAG_NAME, "a")
    
    for link in links:
        href = link.get_attribute('href')
        if not href:
            continue
            
        href = href.lower()
        keywords = ['2023', 'sustainability', 'esg', "impact", "carbon"]
        if '.pdf' in href and any(keyword in href for keyword in keywords):
            print(f"Found PDF: {href}")
            return href
    
    return None

def download_pdf(url, company_name, max_retries=3):
    """下载PDF文件到reports目录，包含重试机制"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/pdf'
    }
    
    # 确保reports目录存在
    if not os.path.exists('./reports'):
        os.makedirs('./reports')
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                verify=False,
                timeout=30  # 添加超时设置
            )
            if response.status_code == 200:
                filename = f"./reports/{company_name}.pdf"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
            
        except requests.exceptions.ConnectionError as e:
            print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 在重试之前等待2秒
                continue
            else:
                print(f"下载PDF失败: {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"下载出错: {str(e)}")
            return None
    
    return None

def write_log(company_name, status):
    """记录公司处理状态到日志文件
    status: 'Success in trail1' / 'Success in trail2' / 'Fail to find'
    """
    with open('crawler_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{company_name}: {status}\n")

def process_company(company_name):
    """处理单个公司的主函数"""
    driver = init_driver()
    
    try:
        # 1. 在Google中搜索PDF
        pdf_url = search_pdf_in_google(company_name, driver)
        if pdf_url:
            pdf_path = download_pdf(pdf_url, company_name)
            if pdf_path:
                text = extract_text_from_pdf(pdf_path)
                if text and ('scope 1' in text.lower() and 'scope 2' in text.lower()):
                    print("PDF contains scope1 and scope2")
                    write_log(company_name, "Success in trail1")
                    return
                else:
                    # 删除不符合要求的PDF
                    os.remove(pdf_path)
        
        # 2. 如果没找到PDF或PDF不包含所需信息，搜索网页
        webpage_url = search_webpage_in_google(company_name, driver)
        if webpage_url:
            pdf_url = find_pdf_in_webpage(webpage_url, driver)
            if pdf_url:
                pdf_path = download_pdf(pdf_url, company_name)
                if pdf_path:
                    text = extract_text_from_pdf(pdf_path)
                    if text and ('scope 1' in text.lower() and 'scope 2' in text.lower()):
                        print("PDF contains scope1 and scope2")
                        write_log(company_name, "Success in trail2")
                        return
                    else:
                        # 删除不符合要求的PDF并记录
                        os.remove(pdf_path)
                        write_log(company_name, f"Found in {webpage_url}, PDF not valid: {pdf_url}")
                        return
            else:
                write_log(company_name, f"Found webpage but no PDF: {webpage_url}")
                return
        
        print(f"No suitable report found for {company_name}")
        write_log(company_name, f"Fail to find in {webpage_url if webpage_url else 'No webpage found'}")
        return
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # 添加开始时间和分割线
    start_time = datetime.now()
    with open('crawler_log.txt', 'a', encoding='utf-8') as f:
        f.write("="*9)
        f.write(f"开始运行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*9 + "\n")

    # 批量处理公司
    with open('1410_test_list.txt', 'r', encoding='utf-8') as file:
        for line in file:
            company_name = line.split('\t')[0].strip()
            if not company_name:
                continue
            
            # 检查reports目录下是否已存在该公司的PDF
            pdf_files = os.listdir('reports')
            company_pdfs = [f for f in pdf_files if company_name.lower() in f.lower()]
            if company_pdfs:
                print(f"\n公司 {company_name} 的PDF已存在,跳过处理")
                continue
                
            print(f"\n处理公司: {company_name}")
            process_company(company_name)
    
    # 添加结束分割线
    with open('crawler_log.txt', 'a', encoding='utf-8') as f:
        f.write("="*50 + "\n")
    
