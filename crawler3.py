import os
import time
import datetime
import urllib.parse
import threading

import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from standardization import extract_text_from_pdf, find_emissions_data
from database import init_connection_pool, get_data, close_connection_pool

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局变量
LOG_FILENAME = None
STATS = None  # 添加全局统计变量

# Helper Function: 写入日志
def write_log(message):
    """写入日志，自动添加时间戳"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

# Helper Function: 初始化 Selenium WebDriver
def init_driver():
    """初始化 Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-blink-features=AutomationControlled') 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    return webdriver.Chrome(options=options)

# Helper Function: 使用selenium获取搜索结果
def get_search_results(driver, company_name, search_url, search_query, max_trials=3):

    for trial in range(max_trials): # 最多尝试3次
        try:
            # 访问搜索页面
            driver.get(search_url)
            wait = WebDriverWait(driver, 30)
            
            search_results = wait.until(
                EC.presence_of_all_elements_located(search_query)
            )
            
            # 检查是否正常获取到搜索结果
            if search_results:
                return search_results
            # 如果没获取到，等待2秒后重试
            time.sleep(2)

        except Exception as e:
            # 如果重试次数未达到最大，等待2秒后重试
            if trial < max_trials - 1:
                time.sleep(2)
                continue
            # 如果重试次数达到最大，写入日志并返回None
            write_log(f"{company_name}: Failed to get search results after {max_trials} attempts: {str(e)}")
            return None
        
    # 如果所有尝试都失败，返回None
    return None

# Helper Function: 下载PDF文件(同时验证PDF内容是否包含scope 1或scope 2)
def download_pdf(url, company_name, max_trials=3):
    
    # 检查是否是pdf的URL
    if 'pdf' not in url:
        write_log(f"{company_name}: Is not a PDF URL | URL: {url}")
        return None
    
    # 设置请求headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/pdf'
    }

    # 创建PDF文件路径
    pdf_path = f"./reports/{company_name}.pdf"

    for trial in range(max_trials): # 最多尝试3次
        
        try:
            # 发送请求
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            
            # 如果请求成功，处理PDF文件
            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                # 检查PDF内容是否包含scope 1或scope 2
                text = extract_text_from_pdf(pdf_path)

                if text == None or text == "":
                    write_log(f"{company_name}: PDF content does not contain 'scope 1' or 'scope 2' | URL: {url}")
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    return None
                else:
                    write_log(f"{company_name}: Valid PDF downloaded | URL: {url}")
                    return pdf_path
        
        except Exception as e:
            # 如果重试次数未达到最大，等待2秒后重试
            if trial < max_trials - 1:
                time.sleep(2)
                continue

            # 如果重试次数达到最大，删除PDF文件
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            write_log(f"{company_name}: PDF Processing Error | Error: {e} | URL: {url}")
            return None
    
    write_log(f"{company_name}: Failed to download PDF after {max_trials} attempts | URL: {url}")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    return None


# 第一步：尝试直接在Bing中搜索PDF
def search_pdf_in_bing(company_name, driver):
    """在Bing中搜索公司的PDF报告，并验证PDF内容是否包含所需信息"""
    
    # 搜索查询语句
    search_query = f"{company_name} sustainability report 2024 pdf -responsibilityreports"
    search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}&first=1&form=QBRE"
    write_log(f"{company_name}: Searching PDF in Bing | URL: {search_url}")

    # 调用helper function获取搜索结果
    search_query = (By.CSS_SELECTOR, '.b_algo h2 a')
    search_results = get_search_results(driver, company_name, search_url, search_query)
    
    if not search_results:
        write_log(f"{company_name}: No Search Results Found | URL: {search_url}")
        return None

    # 从搜索结果中提取PDF链接
    pdf_links = []
    #pdf_indicators = ['.pdf', 'sustainability', 'report', '2024', '2023']
    for result in search_results:
        url = result.get_attribute('href').lower()
        if url and '.pdf' in url:
            pdf_links.append(url)   

    if not pdf_links:
        write_log(f"{company_name}: No PDF Links Found in Search Results | URL: {search_url}")
        return None


    # 检查PDF是否含有scope 1或scope 2 (download_pdf函数会检查)
    for pdf in pdf_links:
        pdf_path = download_pdf(pdf, company_name)
        if pdf_path:
            return pdf_path
        
    write_log(f"{company_name}: No Valid PDF Found in Search Results")
    return None


# 第二步：如果无法直接找到PDF，搜索官网网址
def search_webpage_in_bing(company_name, driver):
    
    # 搜索查询语句
    search_query = f"{company_name} sustainability report -responsibilityreports"
    search_url = f"https://www.bing.com/search?q={urllib.parse.quote(search_query)}&first=1&form=QBRE"
    write_log(f"{company_name}: Searching Webpage in Bing | URL: {search_url}")
        

    # 调用helper function获取搜索结果
    search_query = (By.CSS_SELECTOR, '.b_algo h2 a')
    search_results = get_search_results(driver, company_name, search_url, search_query)

    if not search_results:
        write_log(f"{company_name}: No Search Results Found | URL: {search_url}")
        return None
    
    # 从搜索结果中提取前三个非PDF网页链接
    url_list = []
    count = 0
    
    # 修改这部分代码以处理StaleElementReferenceException
    for result in search_results:
        if count >= 3:
            break
        try:
            url = result.get_attribute('href')
            if url and '.pdf' not in url.lower():
                url_list.append(url)
                count += 1
        except Exception as e:
            write_log(f"{company_name}: Error getting URL from search result: {str(e)}")
            continue

    # 如果没有找到任何有效URL，重试一次
    if not url_list:
        try:
            # 重新加载页面并获取结果
            search_results = get_search_results(driver, company_name, search_url, search_query)
            if search_results:
                for result in search_results:
                    if count >= 3:
                        break
                    try:
                        url = result.get_attribute('href')
                        if url and '.pdf' not in url.lower():
                            url_list.append(url)
                            count += 1
                    except Exception as e:
                        write_log(f"{company_name}: Error getting URL from search result (retry): {str(e)}")
                        continue
        except Exception as e:
            write_log(f"{company_name}: Error during retry: {str(e)}")
            
    return url_list


# 第三步：在官网中找PDF链接
def find_pdf_in_webpage(url, driver, company_name):

    write_log(f"{company_name}: Searching PDF in Webpage | URL: {url}")

    search_query = (By.TAG_NAME, "a")
    search_results = get_search_results(driver, company_name, url, search_query)
    if not search_results:
        write_log(f"{company_name}: No Search Results Found | URL: {url}")
        return None
    # 从搜索结果中提取PDF链接
    pdf_links = []
    for result in search_results:
        try:
            # 获取链接的href属性
            href = result.get_attribute('href')
            if not href:  # 如果href为None或空字符串，跳过
                continue
            # 检查链接是否为pdf
            # response = requests.head(href, allow_redirects=True)
            # is_pdf = ('.pdf' in href.lower() or "application/pdf" in response.headers.get("Content-Type", ""))
            is_pdf = ('.pdf' in href.lower())

            # 获取链接文本是否包含关键词
            text = result.text.lower()
            keywords = ['report', 'esg', 'sustainability', 'impact', 'environment', 'green', 'carbon', 'emissions']
            has_keywords = any(keyword in text for keyword in keywords)
            
            # 检查是否是PDF且包含关键词
            if is_pdf and has_keywords and (href not in pdf_links):
                pdf_links.append(href)
                
        except Exception as e:
            # 如果元素已经过期，继续处理下一个
            continue
    write_log(f"{company_name}: Found {len(pdf_links)} PDF on webpage.")

    if not pdf_links:
        return None

    # 下载并检查前10个pdf
    for pdf in pdf_links[:10]:
        pdf_path = download_pdf(pdf, company_name)
        if pdf_path:
            return pdf_path
    
    write_log(f"{company_name}: No Valid PDF Found in Webpage")
    return None
        
# 处理单个公司
def process_company(company_name):
    print(f"Processing {company_name}...")
    driver = init_driver()
    
    # 1. 直接搜索PDF
    pdf_url = search_pdf_in_bing(company_name, driver)
    if pdf_url:
        with threading.Lock():  # 使用锁保护共享资源访问
            STATS['direct_pdf_success'] += 1
        driver.quit()
        return
    
    # 2. 如果没找到PDF，搜索网页
    webpage_url_list = search_webpage_in_bing(company_name, driver)
    if webpage_url_list:
        for url in webpage_url_list:
            pdf_url = find_pdf_in_webpage(url, driver, company_name)
            if pdf_url: 
                with threading.Lock():  # 使用锁保护共享资源访问
                    STATS['webpage_pdf_success'] += 1
                driver.quit()
                return
    
    # 如果所有方法都失败
    with threading.Lock():  # 使用锁保护共享资源访问
        STATS['failed_companies'].append(company_name)
    driver.quit()

# 处理一个批次的公司
def process_batch(batch_num):
    print(f"\nStarting Batch {batch_num}...")
    
    # 初始化全局统计数据
    global STATS
    STATS = {
        'total_companies': 0,
        'direct_pdf_success': 0,
        'webpage_pdf_success': 0,
        'failed_companies': []
    }
    
    # 创建logs目录（如果不存在）
    os.makedirs('./logs', exist_ok=True)
    
    # 设置全局日志文件名
    global LOG_FILENAME
    LOG_FILENAME = f'./logs/crawler_batch{batch_num}_log.txt'
    summary_filename = f'./logs/crawler_batch{batch_num}_summary.txt'
    
    # 初始化数据库连接
    init_connection_pool()
    
    # 从数据库获取公司列表
    query = "SELECT company_name FROM emissions_data_2336"
    companies = get_data(query)
    
    '''
    # 设置测试批次
    batch_companies = [
        company['company_name'] 
        for i, company in enumerate(companies) 
        if (i > 80) and (i < 120)  # 只取前20个公司
    ]
    '''
    # 获取相应批次的公司列表
    batch_companies = [
        company['company_name'] 
        for i, company in enumerate(companies) 
        if i % 10 == (batch_num - 1)
    ]
    
    
    # 获取已存在的PDF文件列表
    existing_pdfs = {
        os.path.splitext(f)[0] 
        for f in os.listdir('./reports') 
        if f.endswith('.pdf')
    }
    # 过滤掉已经存在PDF的公司
    companies_to_process = [
        company_name 
        for company_name in batch_companies 
        if company_name not in existing_pdfs
    ]

    # 给日志添加开始分割线
    with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
        start_time = datetime.datetime.now()
        f.write("="*50 + "\n")
        f.write(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n")

    STATS['total_companies'] = len(companies_to_process)
    
    '''
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(process_company, company_name)
            for company_name in companies_to_process
        ]
        concurrent.futures.wait(futures)
    '''
    # 不使用线程
    for company_name in companies_to_process:
        process_company(company_name)
    
    # 关闭数据库连接池
    close_connection_pool()
    
    # 生成汇总报告
    with open(summary_filename, 'a', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write(f"Crawler Summary Report - Batch {batch_num}\n")
        f.write(f"Total Companies: {STATS['total_companies']}\n")
        f.write(f"Direct PDF Search Success: {STATS['direct_pdf_success']}\n")
        f.write(f"Webpage PDF Search Success: {STATS['webpage_pdf_success']}\n")
        f.write(f"Failed Companies: {len(STATS['failed_companies'])}\n")
        f.write("\nList of Failed Companies:\n")
        for company in STATS['failed_companies']:
            f.write(f"- {company}\n")
        f.write("\n" + "="*50 + "\n")
    
    # 给日志添加结束分割线
    with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
        end_time = datetime.datetime.now()
        f.write("="*50 + "\n")
        f.write(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n")
    
    print(f"Batch {batch_num} completed")

if __name__ == "__main__":
    # 测试单个公司
    #company_name = "APPLE"
    #process_company(company_name)

    # 正常批处理代码
    batch_num = 3
    process_batch(batch_num)

    '''
    # 测试特定网页
    # 设置日志文件
    os.makedirs('./logs', exist_ok=True)
    LOG_FILENAME = './logs/crawler_test_log.txt'
    
    # 初始化统计数据
    STATS = {
        'total_companies': 1,
        'direct_pdf_success': 0,
        'webpage_pdf_success': 0,
        'failed_companies': []
    }
    
    # 创建reports目录（如果不存在）
    os.makedirs('./reports', exist_ok=True)
    
    # 测试特定网页
    driver = init_driver()
    find_pdf_in_webpage(
        "https://ri.ambev.com.br/en/reports-publications/annual-and-sustainability-report/",
        driver, 
        "AMBEV SA"
    )
    driver.quit()
    '''