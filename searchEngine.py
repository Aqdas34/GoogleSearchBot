import time 
# from selenium import webdriver
import csv
import os
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import random
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager
import openpyxl
import re
excluded = []
def excludeit(w):
    for ex in excluded:    
        if ex in w:
            return False
    return True       


try:
    with open('inputs/excluded.txt', 'r') as key:
        for k in key:
            excluded.append(k.strip())
except:pass            
def clean_keywords(keywords):
    keywords=str(keywords)
    # Replace non-alphabet characters with '+'
    cleaned_keywords = re.sub(r'[^a-zA-Z0-9]', '+', keywords)
    
    # Remove consecutive '+' signs
    cleaned_keywords = re.sub(r'\++', '+', cleaned_keywords)
    
    return cleaned_keywords.strip('+')
# ser = Service(ChromeDriverManager().install())
# options = webdriver.ChromeOptions()
# options.add_argument('--headless')
# browser = webdriver.Chrome(service=ser, options=options)
# browser.implicitly_wait(30)

resultList = []
failRequests=[]



user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    # Add more User-Agent strings here
]


# def google(ur):
#     title=''
#     link=''
#     count=0
#     try:    
#         count=0
#         title= '',
#         link= '',
#         # username = "rbowpoint"
#         # password = "OZPn+O97MGkLa"
#         # proxy = "pr.oxylabs.io:7777"
#         # country = 'US'  # Change this to the desired country code
#         username = "rbowpoint"
#         password = "Alex_007007007"
#         proxy = "pr.oxylabs.io:10000"
#         country = 'us'  # Change this to the desired country code
        
#         # https://customer-rbowpoint:Alex_007007007@us-pr.oxylabs.io:10000
        
#         entry = f'https://customer-{username}:{password}@{country}-{proxy}'
        
#         # entry = f'http://customer-{username}-cc-{country}:{password}@{proxy}'
        
#         proxies = {
#             'http': entry,
#             'https': entry
#         }

#         headers = {
#             'User-Agent': random.choice(user_agents),
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Referer': 'https://www.google.com',
#             'Connection': 'keep-alive'
#         }

#         # link = str(ur).replace(' ', '+').replace('&', '+').replace(',','+')
#         URL_link = f"https://www.google.com/search?q={clean_keywords(ur)}"
#         # https://ip.oxylabs.io/location
#         while count<3:
#             try:
#                 # time.sleep(random.uniform(2,5))
#                 response = requests.get(URL_link, proxies=proxies, headers=headers)
#                 if response.status_code == 429:
#                     print("Recieved errror 429, sleeping for a while")
#                     time.sleep(random.uniform(30,60))   # changes  made
#                     continue
#                 # response = requests.get(URL_link, headers=headers)
#             except Exception as e:
#                 print(str(e))
                
                
#                 # return
#             # response=''
#             if response.status_code == 200:
#                 soup = BeautifulSoup(response.content, 'html.parser')
#                 # print(soup.prettify())
#                 results = soup.find_all('div', class_='MjjYud')
                
#                 if len(results) <=1:
#                       results = soup.find_all('div', class_='yuRUbf')
#                 for result in results:
#                     try:
#                         title_tag = result.find('h3')
#                         if title_tag:
#                             title = title_tag.get_text()
#                             link = result.find('a')['href']
#                             # print(f'Title: {title}')
#                             # print(f'URL: {link}')
#                             if excludeit(link):  # Assuming excludeit function is defined elsewhere
#                                 item = {
#                                     "keyword": ur,
#                                     "title": title,
#                                     "link": link,
#                                 }
#                                 # print(item)
#                                 resultList.append([ur, title, link])
#                                 return [ur, title, link]
                                
#                     except Exception as e:
#                         print(f'Error parsing result: {e}')
#                 count=5        
                       
                
#             else:
#                 count+=1
#                 # failRequests.append(ur)
#                 link=response.status_code
#                 print(f'Failed to retrieve search results: {response.status_code}')
#     except:pass  
#     return [ur, 'title', 'error429']


def google(ur):
    title = ''
    link = ''
    count = 0
    try:
        count = 0
        title = ''
        link = ''
        username = "rbowpoint"
        password = "Alex_007007007"
        proxy = "pr.oxylabs.io:10000"
        country = 'us'  # Change this to the desired country code
        
        entry = f'https://customer-{username}:{password}@{country}-{proxy}'
        
        proxies = {
            'http': entry,
            'https': entry
        }

        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com',
            'Connection': 'keep-alive'
        }

        # Test the proxy connection
        test_url = "https://www.google.com"
        try:
            test_response = requests.get(test_url, proxies=proxies, headers=headers, timeout=10)
            if test_response.status_code == 200:
                print("Proxy is connected successfully.")
            else:
                print(f"Failed to connect via proxy, status code: {test_response.status_code}")
                return [ur, 'title', 'proxy_error']
        except Exception as e:
            print(f"Error connecting to proxy: {e}")
            return [ur, 'title', 'proxy_error']

        URL_link = f"https://www.google.com/search?q={clean_keywords(ur)}"
        
        while count < 3:
            try:
                response = requests.get(URL_link, proxies=proxies, headers=headers)
                if response.status_code == 429:
                    print("Received error 429, sleeping for a while")
                    time.sleep(random.uniform(30, 60))
                    continue
            except Exception as e:
                print(f"Error during request: {e}")
                continue

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = soup.find_all('div', class_='MjjYud')
                
                if len(results) <= 1:
                    results = soup.find_all('div', class_='yuRUbf')
                
                for result in results:
                    try:
                        title_tag = result.find('h3')
                        if title_tag:
                            title = title_tag.get_text()
                            link = result.find('a')['href']
                            if excludeit(link):  # Assuming excludeit function is defined elsewhere
                                item = {
                                    "keyword": ur,
                                    "title": title,
                                    "link": link,
                                }
                                resultList.append([ur, title, link])
                                return [ur, title, link]
                                
                    except Exception as e:
                        print(f'Error parsing result: {e}')
                count = 5        
                
            else:
                count += 1
                link = response.status_code
                print(f'Failed to retrieve search results: {response.status_code}')
    except Exception as e:
        print(f"General error: {e}")
    return [ur, 'title', 'error429']


def main(urls):  
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(google, urls)


def write_to_excel(data, file_path):
    try:
        while True:
            try:
                workbook = openpyxl.load_workbook(file_path)
                break
            except FileNotFoundError:
                workbook = openpyxl.Workbook()
                break
            except PermissionError:
                time.sleep(10)

        sheet = workbook.active
        for row in data:
            sheet.append(row)
        workbook.save(file_path)
    except Exception as e:
        print(f"An error occurred: {e}")

def write_to_csv(data, file_path):
    try:
        file_exists = os.path.isfile(file_path)
        while True:
            try:
                with open(file_path, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    if not file_exists:
                        header = ['Searched Keyword', 'Title', 'Website']
                        writer.writerow(header)
                    for row in data:
                        writer.writerow(row)
                break
            except PermissionError:
                time.sleep(10)
    except Exception as e:
        print(e)
        pass        


# def Google(ur):
    # try:
    #     title=''
    #     anchor=''
    #     link=str(ur).replace(' ','+').replace('&','+')
    #     URL_link = f"https://www.google.com/search?q={link}"
    #     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
    #     browser.get(URL_link)
    #     time.sleep(1)
    #     results = browser.find_elements(By.XPATH, '//div[@class="MjjYud"]')
    #     for result in results:
    #         try:
    #             title=''
    #             anchor=''
    #             title = result.find_element(By.XPATH, './/h3').text
    #             anchor = result.find_element(By.XPATH, './/a').get_attribute('href')
    #             if excludeit(anchor):
    #                 item = {
    #                     "keyword": ur,
    #                     "title": title,
    #                     "link": anchor,
    #                 }
    #                 print(item)
    #                 resultList.append([ur, title, anchor])
    #                 break 
    #         except Exception as e:
    #             print(e)  
    # except Exception as e:
    #     print(e)
    #     pass
           
def get_result_list():
    return resultList
def set_excluded_domains(domains):
    global excluded
    for dm in domains:
        if not dm in excluded:
           excluded.append(dm)
# def download(file_name, file_type):
#     if file_type.lower() == 'csv':
#         write_to_csv(resultList, f"{file_name}.csv")
#     elif file_type.lower() == 'xlsx':
#         write_to_excel(resultList, f"{file_name}.xlsx")
