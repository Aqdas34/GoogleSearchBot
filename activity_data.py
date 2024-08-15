import requests
import uuid
import time
def send_activity_data(project_name,project_id, employee_id, spent_time, start, end, total_searched_keywords):
    url = f"https://autofyn.com/activities"
    params = {
        'project_name': project_name,
        'project_id':project_id,
        'employee_id': employee_id,
        'spent_time': spent_time,
        'start': start,
        'end': end,
        'total_searched_keywords': total_searched_keywords
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        # print("Data sent successfully!")
        return response.json()
    else:
        print(f"Failed to send data. Status code: {response.status_code}")
        return response.text
def fetch_app_data(project_id,mac):
    # response = requests.get('http://autofyn.com/appCms/content')
    # 04-EC-D8-4A-1D-24
    url = f"https://autofyn.com/appCms/content"
    # http://127.0.0.1:8000/appCms/content?project_id=1&mac=00:1B:44:11:3A:B7
    params = {
        'project_id': project_id,
        'mac':mac
    }
    # print(mac)
    # print(f"{project_id}/{mac}")
    
    
    response = requests.get(url, params=params)
    # print(response.json)
    
    if response.status_code == 200:
        # print("Data sent successfully!")
        # print(response.json())
        return response.json()
    else:
        print(f"Failed to send data. Status code: {response.status_code}")
        return response.text

# def fetch_app_data(project_id, mac, max_retries=5, initial_wait_time=2, backoff_multiplier=2):
#     url = "https://autofyn.com/appCms/content"
#     params = {
#         'project_id': project_id,
#         'mac': mac
#     }
    
#     retries = 0
#     wait_time = initial_wait_time
    
#     while retries < max_retries:
#         response = requests.get(url, params=params)
        
#         if response.status_code == 200:
#             return response.json()
#         elif response.status_code == 429:
#             retries += 1
#             retry_after = response.headers.get('Retry-After')
#             if retry_after:
#                 wait_time = int(retry_after)
#             print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
#             time.sleep(wait_time)
#             wait_time *= backoff_multiplier  # Exponential backoff
#         else:
#             print(f"Failed to fetch data. Status code: {response.status_code}")
#             return response.text
    
#     print("Max retries exceeded.")
#     return None

def get_mac_address():
    # Get the MAC address as a 48-bit positive integer
    mac_num = uuid.getnode()
    
    # Convert the integer to a hexadecimal string and format it as a MAC address
    mac_address = ':'.join(('%012x' % mac_num)[i:i+2] for i in range(0, 12, 2))
    mac_address=mac_address.upper().replace(':','-')
    return mac_address
# # Example usage
# project_id=1
# mac='DC-71-96-9E-09-08'
# # DC:71:96:9E:09:0C
# CMS_app=fetch_app_data(project_id,mac)
# user_data = CMS_app.get('user', {})
# app_content = CMS_app.get('data', {})
# email = user_data.get('email')
# print(email)
# print(app_content)
# base_url = "http://your-laravel-app.com"
# project_name = "Google Search Scraper"
# employee_id = 1
# project_id=4
# spent_time = 120  # in minutes
# start = "2024-07-11 22:08:41"
# end = "2024-07-11 22:08:41"
# # 2024-07-12 10:31:18 2024-07-12 10:31:29
# total_searched_keywords = 300
# send_activity_data(project_name,project_id, employee_id, spent_time, start, end, total_searched_keywords)

