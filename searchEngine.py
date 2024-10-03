import json
import time 
import csv
import os
import requests
from bs4 import BeautifulSoup
import concurrent.futures

from RavaDynamics import load_excluded_domains
import openpyxl
import re
from urllib.parse import urlparse
import requests

from RavaDynamics import get_device_id
from activity_data import fetch_app_data



def get_domain_name(url):
    parsed_url = urlparse(url if url.startswith('http') else f'http://{url}')
    domain = parsed_url.netloc
    # Remove 'www.' prefix if present
    domain = domain.lstrip('www.')
    return domain



# Example usage
def load_excluded_domains_two():
    # URL to fetch data
    url = "https://autofyn.com/excluded_domains/fetch_excluded_domains.php"
    
    try:
        # Making a GET request to fetch the JSON data
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        
        # Parsing the JSON response
        data = response.json()
        
        # Extracting domain_name from the JSON data
        domain_names = [item['domain_name'] for item in data]
        
        domain_names.append("en.wikipedia.org")
        
        return domain_names
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []




excluded = None

# print(excluded)
def excludeit(w):
    global excluded
    excluded = load_excluded_domains_two()
    # print(f"link = {w}")
    # print(f"excluded = {excluded}")
    w = get_domain_name(w)
    # print(f"after = {w}" )
    
    # print(f"w = {w}")
    if w not in excluded:
        
        return False
    
    # print("False")
    
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


resultList = []
failRequests=[]




import json
import requests


def google(ur):
    title = ''
    link1 = None
    link2 = None
    link3 = None
    rating_count = None
    phone = None
    address = None


    mac = get_device_id()
    # print(mac)
    CMS_app = fetch_app_data(1, mac)
    
    try:
        # Define the search query payload
        payload = json.dumps({
            "q": ur  # Search query term
        })
        
        # print(CMS_app["data"]["API"])
        # Define the headers with the API key
        headers = {
            'X-API-KEY': CMS_app["data"]["API"],
            'Content-Type': 'application/json'
        }
        
        # Make the POST request to the serper.dev API
        response = requests.post("https://google.serper.dev/search", headers=headers, data=payload)
        
        # Check if the response is successful
        if response.status_code == 200:
            data = response.json()
            
            # Check if knowledgeGraph exists
            knowledge_graph = data.get("knowledgeGraph", {})
            if knowledge_graph:
                title = knowledge_graph.get('title', '')
                link1 = knowledge_graph.get('website', None)
                
                # Extract additional fields if they exist
                rating_count = knowledge_graph.get('ratingCount', None)
                address = knowledge_graph.get('attributes', {}).get('Address', None)
                
                # Fetch and split the phone numbers, keeping only the first one
                phone_list = knowledge_graph.get('attributes', {}).get('Phone', None)
                if phone_list:
                    phone = phone_list.split('⋅')[0].strip()  # Take the first phone number
                
                # Call excludeit function to exclude the link, not the title
                if link1 and not excludeit(link1):
                    # Return the formatted list including the additional fields
                    return [ur, title, link1, link2, link3, address, rating_count, phone]
            
            # Extract results from the organic section if no knowledgeGraph is present
            results = data.get("organic", [])
            
            # Get the top three non-wikipedia links
            count = 0
            for result in results:
                link = result.get('link', None)
                
                # Call excludeit function on the link
                if link and not excludeit(link):
                    if count == 0:
                        title = result.get('title', None)
                        link1 = link
                    elif count == 1:
                        link2 = link
                    elif count == 2:
                        link3 = link
                    
                    count += 1
                
                # Stop after collecting 3 valid links
                if count >= 3:
                    break
            
            # Return the formatted list with up to three valid links
            return [ur, title, link1, link2, link3, address, rating_count, phone]
        else:
            print(f"Failed to retrieve search results: {response.status_code}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # In case of failure or no valid links found
    return [ur, title, link1, link2, link3, address, rating_count, phone]



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



           
# def get_result_list():
#     return resultList
def set_excluded_domains(domains):
    excluded = load_excluded_domains()
    for dm in domains:
        if not dm in excluded:
           excluded.append(dm)
