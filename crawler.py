import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import time
import urllib.parse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ReportCrawler:
    def __init__(self):
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化 Selenium
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用日志
        # 添加以下选项来抑制警告
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--log-level=3')  # 只显示严重错误
        options.add_argument('--silent')
        # 禁用所有设备
        options.add_argument('--disable-usb-devices')
        options.add_argument('--disable-dev-tools')
        
        self.driver = webdriver.Chrome(options=options)
        
        # 更新请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def find_report_page_or_pdf(self, company_name):
        """搜索公司最新的可持续发展报告，返回PDF链接或网页链接"""
        # 首先尝试搜索PDF文件
        search_query = f"{company_name} sustainability report 2023 pdf -responsibilityreports"
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
        
        try:
            # 移除 Accept-Encoding 头，让 requests 自动处理编码
            headers = self.headers.copy()
            if 'Accept-Encoding' in headers:
                del headers['Accept-Encoding']
            
            response = requests.get(
                search_url, 
                headers=headers,
                allow_redirects=True
            )
            response.encoding = 'utf-8'  # 确保使用正确的编码
            
            print("Response URL:", response.url)  # 打印最终URL，检查是否被重定向
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试不同的选择器
            search_results = soup.select('div.g')  # 更通用的选择器
            if not search_results:
                search_results = soup.select('div.yuRUbf')
            if not search_results:
                search_results = soup.find_all('div', attrs={'class': 'g'})
            
            print("Found results:", len(search_results))
            
            # 如果使用普通请求方式失败，尝试使用 Selenium
            if len(search_results) == 0:
                print("Trying with Selenium...")
                self.driver.get(search_url)
                time.sleep(3)  # 等待页面加载
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                search_results = soup.select('div.g')
                print("Selenium found results:", len(search_results))
            
            # 检查前两个链接是否为PDF
            for i, result in enumerate(search_results[:2]):
                link = result.find('a')
                if link:
                    url = link.get('href')
                    print(url)
                    if not url:
                        continue
                    url_lower = url.lower()
                    # 修改PDF判断逻辑，考虑URL参数
                    if '.pdf' in url_lower and url_lower.split('?')[0].endswith('.pdf'):
                        return {'type': 'pdf', 'url': url}

            print("No PDF found, searching for sustainability page...")
            
            # 如果没有找到PDF，尝试搜索一般的可持续发展信息
            search_query = f"{company_name} sustainability report -responsibilityreports"
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            print("search_url", search_url)
            
            response = requests.get(
                search_url, 
                headers=headers,
                allow_redirects=True
            )
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.select('div.g')
            print("Found results:", len(search_results))
            if not search_results:
                search_results = soup.select('div.yuRUbf')
            if not search_results:
                search_results = soup.find_all('div', attrs={'class': 'g'})
            
            if len(search_results) == 0:
                self.driver.get(search_url)
                time.sleep(3)
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                search_results = soup.select('div.g')
            
            for result in search_results:
                link = result.find('a')
                if link:
                    url = link.get('href')
                    print(url)
                    if not url:
                        continue
                    url_lower = url.lower()
                    # 同样修改这里的PDF判断逻辑
                    if '.pdf' in url_lower and url_lower.split('?')[0].endswith('.pdf'):
                        return {'type': 'pdf', 'url': url}
                    # 如果是网页链接，返回用于进一步搜索
                    else:
                        return {'type': 'webpage', 'url': url}
            
            return None
        except Exception as e:
            self.logger.error(f"搜索报告失败: {str(e)}")
            return None

    def find_pdf_link(self, url):
        """在页面中查找PDF下载链接"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                wait = WebDriverWait(self.driver, 15)
                
                # 等待页面加载完成
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(3)
                
                # 尝试滚动页面以加载更多内容
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 获取页面上所有链接
                links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(links)} links on attempt {attempt + 1}")
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if not href:
                            continue
                        
                        href = href.lower()
                        # 修改PDF判断逻辑
                        if '.pdf' in href and href.split('?')[0].endswith('.pdf') and \
                           any(keyword in href for keyword in ['2023', 'sustainability', 'esg', 'impact']):
                            print(f"Found PDF link: {href}")
                            return href
                            
                    except Exception as e:
                        print(f"Error processing link: {e}")
                        continue

                if attempt < max_retries - 1:
                    print(f"Retry attempt {attempt + 1} failed, trying again...")
                    time.sleep(2)
                else:
                    print("All retry attempts failed")
                    return None

            except Exception as e:
                self.logger.error(f"查找PDF链接时出错 (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None

        return None

    def download_report(self, url, company_name):
        """下载报告"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 添加更多的请求头，模拟真实浏览器
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/x-pdf',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Referer': url
                }
                
                # 设置较长的超时时间
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    filename = f"{company_name}_sustainability_report_2023.pdf"
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return filename
                    
            except Exception as e:
                self.logger.error(f"下载报告失败 (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # 失败后等待5秒再重试
                    continue
                
        return None

    def crawl(self, company_name):
        """主要爬虫流程"""
        try:
            # 1. 搜索报告页面或PDF
            result = self.find_report_page_or_pdf(company_name)
            if not result:
                self.logger.error(f"无法找到 {company_name} 的报告")
                return None

            # 2. 如果直接找到PDF，直接下载
            if result['type'] == 'pdf':
                return self.download_report(result['url'], company_name)
            
            # 3. 如果是网页，在页面中查找PDF链接
            pdf_link = self.find_pdf_link(result['url'])
            if not pdf_link:
                self.logger.error(f"无法找到PDF下载链接")
                return None

            # 4. 下载报告
            return self.download_report(pdf_link, company_name)

        except Exception as e:
            self.logger.error(f"爬取过程出错: {str(e)}")
            return None

        finally:
            self.driver.quit()

if __name__ == "__main__":
    '''

SALESFORCE: 逆子 下载按钮放在了shadow root里 纯畜
SEB: 逆子 下载按钮是一个跳转链接 纯畜
DIASORIN:    逆子 把数据放4页的Carbon Reduction Plan里 纯畜

BCE INC: 会下到summary report

ZURICH INSURANCE GROUP: bug fixed
F5	bug fixed (responsiblity report提供了一个垃圾report然后被爬了)
'''
    
    crawler = ReportCrawler()
    company_name = "SWATCH GROUP NAM"
    result = crawler.crawl(company_name)
    
    if result:
        print(f"报告已下载: {result}")
    else:
        print("未能找到或下载报告")
    '''
    # 读取公司列表文件
    with open('1410_test_list.txt', 'r', encoding='utf-8') as file:
        # 处理每一行
        for line in file:
            # 提取公司名（从行首到第一个制表符）
            company_name = line.split('\t')[0].strip()
            if not company_name:  # 跳过空行
                continue
                
            print(f"\n正在处理公司: {company_name}")
            
            # 创建新的爬虫实例（因为每次都会在finally中关闭driver）
            crawler = ReportCrawler()
            result = crawler.crawl(company_name)
            
            if result:
                print(f"报告已下载: {result}")
            else:
                print(f"未能找到或下载 {company_name} 的报告")
    '''
