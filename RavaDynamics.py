import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QFormLayout, QFrame, QTextEdit, QComboBox, QScrollArea, QSizePolicy,QDesktopWidget,
    QDialog, QMessageBox,QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QMovie,QFontDatabase,QFont
from PyQt5.QtCore import QSize
import csv
import pandas as pd
import searchEngine
import requests
import activity_data
import concurrent
import rearrange
import os
import concurrent.futures
import datetime 
import webbrowser
import json

import platform


shared_excluded_list = []



API_UPDATE_URL = "https://autofyn.com/storage/app/public/App_CMS_images/get_latest_versioon.txt"  # Replace with your API URL

is_register = False

current_version = None
latest_version = None
def check_for_updates():
    global current_version
    global latest_version
    current_version_path = "version.txt"
    
    if not os.path.exists(current_version_path):
        return None
    
    with open(current_version_path, 'r') as file:
        version_data = json.load(file)
        current_version = version_data.get("version")
    
    
    

    latest_version = requests.get(API_UPDATE_URL)
    if latest_version.status_code == 200:
        
        latest_version_info = latest_version.json()
        latest_version_no = latest_version_info.get("version")
        if latest_version_no > current_version:
            return latest_version_info
    return None



#  pyinstaller --noconsole --onefile --icon=logo.jpg .\RavaDynamics.py








def load_excluded_domains():
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
        
        return domain_names
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


def fetch_app_data():
    response = requests.get('https://autofyn.com/appCms/1/content')
    if response.status_code == 200:
        return response.json()['data']
    else:
        raise Exception("Failed to fetch data from the website")

def generate_dynamic_qss(app_data):
    background_color = app_data.get('color_background', '#f0e6e7')
    button_hover_color = app_data.get('color_button_text_hover', '#7e221b')
    footer_text_color = app_data.get('color_footer_text', '#000000')
    color_input_border = app_data.get('color_input_border', '#000000')
    color_button = app_data.get('color_button', '#000000')
    color_text = app_data.get('color_text', '#000000')
    color_button_text = app_data.get('color_button_text', '#000000')

    qss_content = f"""
    /* General */
    QWidget {{
        font-family: 'Montserrat', sans-serif;
        margin: 0;
        padding: 0;
        background-color: {background_color};
        color: {color_text};
        font-weight: 600;
    }}
    QDialog QLabel {{
        background-color: {background_color};
        color: {color_text};
    }}
    
    /* Main content */
    #logo {{
        padding-top: 10px;
    }}
    #main_content {{
        background-color: {background_color};
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 4px;
        padding-top: 4px;
        margin-left: 10px;
        margin-right: 10px;
        border-radius: 8px;
    }}

    QLabel {{
        background-color: {background_color};
        color: {color_text};
        font-size: 14px;
    }}
    #loading_modal {{
        background-color: {background_color};
        color: {color_text};
        border: 1px solid {color_button};
    }}

    QLineEdit, QTextEdit, QComboBox {{
        border: 2px solid {color_input_border};
        border-radius: 4px;
        padding: 8px;
        width: 100%;
    }}

    QLineEdit, QTextEdit, QComboBox {{
        background-color: {background_color};
    }}

    QPushButton {{
        background-color: {color_button};
        color: {color_button_text};
        padding: 5px 10px;
        border-radius: 4px;
        min-width: 100px;
        white-space: nowrap; /* Prevent text from wrapping */
    }}

    QPushButton:hover {{
        background-color: {button_hover_color};
    }}
    #output_folder_button {{
        min-width: 150px;
        white-space: nowrap; /* Prevent text from wrapping */
    }}

    #output_format {{
        width: 90px;
        background-color: {color_button};
        color: {color_button_text};
        font-size: 14px;
        padding: 3px;
    }}

    /* Error Labels */
    #error {{
        color: {color_button};
    }}

    /* Footer */
    #footer {{
        text-align: center;
        margin-top: 1px;
        font-size: 12px;
        color: {footer_text_color};
        padding-bottom: 4px;
    }}

    /* Scroll Area */
    #excluded_domains_box {{
        border: 2px solid {color_input_border};
        border-radius: 4px;
        min-height: 100px;
    }}
    """
    return qss_content




def get_pixmap_from_url(url):
    newurl=str(url).replace('storage/','storage/app/public/')
    response = requests.get(f'https://autofyn.com/{newurl}')
    if response.status_code == 200:
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        return pixmap
    else:
        return None    

class WorkerThread(QThread):
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    results=[]
    def __init__(self, urls, main_window):
        super().__init__()
        self.urls = urls
        self._is_running = True
        self.main_window = main_window
        self.executor = None

    def run(self):
        self.progress_signal.emit(0)  # Initial progress signal
        # Initialize the ThreadPoolExecutor
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)
        futures = {}
        self.results = [None] * len(self.urls)  # Pre-allocate the list for results

        try:
            # Submit tasks to the executor and store the future with its index
            for i, url in enumerate(self.urls):
                future = self.executor.submit(self.scrape, url)
                futures[future] = i

            for future in concurrent.futures.as_completed(futures):
                if not self._is_running:
                    break
                try:
                    result = future.result()
                    index = futures[future]
                    self.results[index] = result
                    self.main_window.result_count += 1
                    self.progress_signal.emit(self.main_window.result_count)
                except Exception as e:
                    print(f"Task exception: {e}")
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            if self.executor:
                self.executor.shutdown(wait=False)
            # self.main_window.results = self.results
            if self.main_window.download_data():
                self.update_signal.emit("Scraping complete.")
            else:
                self.update_signal.emit("Scraping stopped.")
            self._is_running = False

    def scrape(self, url):
        if not self._is_running:
            return None
        return searchEngine.google(url)

    def stop(self):
        self._is_running = False
        if self.executor:
            self.executor.shutdown(wait=False)
        self.quit()
        self.wait()


# pyinstaller --noconsole --onefile --icon=logo.jpg .\RavaDynamics.py
class MainWindow(QMainWindow):
    def __init__(self,app_data):
        
        
        self.scraping_running = False

        super().__init__()
        self.initialize_directories_and_files()
        font_id = QFontDatabase.addApplicationFont('res/Montserrat-ExtraLight.ttf')
        font_family = None
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        default_font = QFont(font_family)  # Set default font size (e.g., 10)
        QApplication.setFont(default_font)
        
        font_url = 'https://autofyn.com/public/fonts/Montserrat-ExtraLight.ttf'  # Replace with your actual font URL
        response = requests.get(font_url)
        if response.status_code == 200:
            font_data = response.content
            font_id = QFontDatabase.addApplicationFontFromData(font_data)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            default_font = QFont(font_family)
            # default_font.setPointSize(18)
            QApplication.setFont(default_font)
        self.setWindowTitle(app_data.get('text_1'))
        screen_resolution = QDesktopWidget().availableGeometry()
        window_width = int(screen_resolution.width() * 0.7)
        window_height = int(screen_resolution.height() * 0.7)
        # # Center the window on the screen
        self.setGeometry(
            (screen_resolution.width() - window_width) // 2,
            (screen_resolution.height() - window_height) // 2,
            window_width,
            window_height
        )
        # print(f"parent = {self.geometry()}")
        self.center()
        
        icon_pixmap = get_pixmap_from_url(app_data['image_1'])
        if icon_pixmap:
            scaled_icon = icon_pixmap.scaled(100, 100, Qt.KeepAspectRatio)
            self.setWindowIcon(QIcon(scaled_icon))
        if (app_data.get('text_4')):
            QTimer.singleShot(16000, lambda: self.show_notification(app_data.get('text_4')))
            
        # Changed made
        self.output_folder=''
        self.user_data=''
        self.app_data=app_data
        self.excluded_domains = load_excluded_domains()
        self.add_excluded_domains = 0
        
        

        self.worker_thread = None
        self.total_keywords = 0
        self.result_count = 0
        self.estimated_time = 0
        self.start_time=''
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout()
        header.setFixedHeight(160)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header.setLayout(header_layout)

        logo = QLabel()
        logo.setObjectName("logo")
        logo_pixmap = get_pixmap_from_url(app_data['image_2'])
        if logo_pixmap:
            # self.setWindowIcon(QIcon(icon_pixmap))
            logo.setPixmap(logo_pixmap.scaled(140, 140, Qt.KeepAspectRatio))
        # Add logo to header layout and center it
        header_layout.addStretch(1)  # Pushes logo to the center
        header_layout.addWidget(logo)
        header_layout.addStretch(1)

        nav = QFrame()
        nav.setObjectName("header")
        nav_bar = QHBoxLayout()
        nav.setFixedHeight(15)
        nav_bar.setContentsMargins(0, 0, 0, 0)
        nav.setLayout(nav_bar)
        version = QLabel(app_data.get('text_3'))
        version.setObjectName("version")
        # version.setFixedHeight(20)
        version.setAlignment(Qt.AlignCenter)
        nav_bar.addWidget(version)
        btn_download = QPushButton("Download")
        btn_download.setObjectName("btnDownload")
        btn_download.clicked.connect(self.download_data)
        main_layout.addWidget(header)
        main_layout.addWidget(nav)
        main_content = QFrame()
        main_content.setObjectName("main_content")
        main_content_layout = QVBoxLayout()
        main_content.setLayout(main_content_layout)
        
        form_group = QFormLayout()
        
        search_terms_label = QLabel("Search Terms:")
        self.search_terms = QTextEdit()
        self.search_terms.setLineWrapMode(QTextEdit.NoWrap)
        self.search_terms.setObjectName("search_terms")
        form_group.addRow(search_terms_label, self.search_terms)

        excluded_domains_label = QLabel("Excluded Domains:")
        # excluded_domains_label.setFont(QFont(font_family, 12))
        self.excluded_domains_box = QScrollArea()
        self.excluded_domains_box.setObjectName("excluded_domains_box")
        self.excluded_domains_box.setWidgetResizable(True)
        self.excluded_domains_widget = QWidget()
        self.excluded_domains_layout = QVBoxLayout(self.excluded_domains_widget)
        self.excluded_domains_box.setWidget(self.excluded_domains_widget)
        # self.excluded_domains_box.setFixedHeight(100)
        form_group.addRow(excluded_domains_label, self.excluded_domains_box)
        
        
        
        add_domain_container = QHBoxLayout()
        self.Add_new_domain = QLabel("Add new domains :")
        self.new_domain = QLineEdit()
        self.new_domain.setObjectName("new_domain")
        self.new_domain.setPlaceholderText("Add new domain")
        add_domain_button = QPushButton("Exclude")
        add_domain_button.setObjectName("add_domain_button")
        add_domain_button.clicked.connect(self.add_domain)
        add_domain_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        add_domain_container.addWidget(self.Add_new_domain)
        add_domain_container.addWidget(self.new_domain)
        add_domain_container.addWidget(add_domain_button)
        form_group.addRow(add_domain_container)
        output_filename_label = QLabel("Output Filename:")
        self.output_filename = QLineEdit()
        self.output_filename.setObjectName("output_filename")
        form_group.addRow(output_filename_label, self.output_filename)
        main_content_layout.addLayout(form_group)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        output_folder_button = QPushButton("Select Folder")
        output_folder_button.setObjectName("output_folder_button")
        output_folder_button.clicked.connect(self.select_output_folder)
        self.output_format = QComboBox()
        self.output_format.addItems(["CSV", "XLSX"])
        self.output_format.setObjectName("output_format")
        buttons_layout.addWidget(self.output_format) 
        buttons_layout.addWidget(output_folder_button)
        
        
        
        
        # Create buttons
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.start_scraping)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.clicked.connect(self.stop_scraping)
        

        
        # Add buttons to buttons_layout
        buttons_layout.addWidget(self.btn_start)
        buttons_layout.addWidget(self.btn_stop)
    
        
        main_content_layout.addLayout(buttons_layout)
        logo_footer_layout = QHBoxLayout()
        logo_footer = QLabel()

        logo_footer.setObjectName("logo_footer")
        logo_pixmap_footer = get_pixmap_from_url(app_data['image_3'])
        if logo_pixmap_footer:
            # self.setWindowIcon(QIcon(icon_pixmap))
            logo_footer.setPixmap(logo_pixmap_footer.scaled(150, 150, Qt.KeepAspectRatio))
        


        logo_footer_layout.addWidget(logo_footer)
        logo_footer_layout.setAlignment(Qt.AlignCenter)
        
        main_content_layout.addLayout(logo_footer_layout)
        main_layout.addWidget(main_content)
        footer = QLabel(app_data.get('text_2'))
        footer.setObjectName("footer")
        footer.setFixedHeight(40)
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    
    def update_button_state(self):
        self.btn_stop.setEnabled(self.scraping_running)


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def show_notification(self, message):
        QMessageBox.warning(self, "Info", message)
    def select_output_folder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", options=options | QFileDialog.ShowDirsOnly)
        os_name = platform.system()
        if selected_folder:
            if os_name == "Windows":
                
                if selected_folder.startswith('C:') and not (selected_folder.endswith('Desktop') or selected_folder.endswith('Documents') or selected_folder.endswith('Downloads')):
                    QMessageBox.warning(self, "Warning", "File cannot be saved in C: drive, except in Desktop or Documents. Please select a valid folder.")
                else:
                    # Store the selected folder path in the class attribute
                    self.output_folder = selected_folder
            else:
                self.output_folder = selected_folder
            # self.output_filename.setText(selected_folder)  # Optionally, show the selected folder path in the QLineEdit
    def add_domain(self):
        new_domain_text = self.new_domain.text().strip()
        if new_domain_text:
            self.excluded_domains.insert(0,new_domain_text)
            self.add_excluded_domains += 1
            # print(self.excluded_domains)
            self.new_domain.clear()
            self.update_excluded_domains_box()
            searchEngine.set_excluded_domains(self.excluded_domains)

    def update_excluded_domains_box(self):
        for i in reversed(range(self.excluded_domains_layout.count())):
            widget = self.excluded_domains_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        for doamin_index in range(self.add_excluded_domains-1,-1,-1):
            domain_item = QHBoxLayout()
            domain_item.setSpacing(0)  # Remove spacing between label  button
            domain_item.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout
            domain_label = QLabel(self.excluded_domains[doamin_index])
            domain_label.setObjectName("domain_label")
            remove_button = QPushButton("Remove")
            remove_button.setObjectName(f"remove_button_{self.excluded_domains[doamin_index]}")
            remove_button.clicked.connect(lambda checked, domain=self.excluded_domains[doamin_index]: self.remove_domain(domain))
            remove_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            remove_button.setMaximumWidth(130)
            domain_item.addWidget(domain_label)
            domain_item.addWidget(remove_button)
            domain_container = QWidget()
            domain_container.setLayout(domain_item)
            self.excluded_domains_layout.addWidget(domain_container)

    def remove_domain(self, domain):
        if domain in self.excluded_domains:
            self.excluded_domains.remove(domain)
            self.add_excluded_domains -= 1
            self.update_excluded_domains_box()
            searchEngine.set_excluded_domains(self.excluded_domains)

    def start_scraping(self):
        global shared_excluded_list
        shared_excluded_list= self.excluded_domains[::-1]
        self.scraping_running = True
        # self.update_button_state()
        if not self.user_status():
            QMessageBox.warning(self, "Danger", "Please contact the admin. You are not eligible to use this app.")
            return
        self.initialize_directories_and_files()
        filename = self.output_filename.text().strip()
        if not filename:
            QMessageBox.warning(self, "Warning", "Please enter a valid filename.")
            return
        if not self.output_folder:
            QMessageBox.warning(self, "Warning", "Please Select the Folder.")
            return
        self.start_time = datetime.datetime.now().replace(microsecond=0)
        search_terms = self.read_keywords_from_file()
        ui_search_terms = self.search_terms.toPlainText().strip().split('\n')
        search_terms.extend(ui_search_terms)
        search_terms = list(filter(None, search_terms))

        if not search_terms:
            QMessageBox.warning(self, "Warning", "No keywords found in keywords.txt or search terms input.")
            return

        self.total_keywords = len(search_terms)
        self.result_count = 0
        self.estimated_time = int(self.total_keywords/50)*7 +10  # Assuming 5 seconds per keyword
        self.timer.start(1000)  # Update time every second

        self.worker_thread = WorkerThread(search_terms, self)
        self.worker_thread.update_signal.connect(self.update_status)
        self.worker_thread.start()
        self.show_loading_modal()
    def initialize_directories_and_files(self):
        # Define the folder paths
        inputs_folder = "inputs"
        outputs_folder = "outputs"

        # Check and create inputs folder
        if not os.path.exists(inputs_folder):
            os.makedirs(inputs_folder)
            # print(f"Created folder: {inputs_folder}")

        # Check and create outputs folder
        if not os.path.exists(outputs_folder):
            os.makedirs(outputs_folder)
            # print(f"Created folder: {outputs_folder}")

        # Define the file paths
        keywords_file = os.path.join(inputs_folder, "keywords.txt")
        excluded_file = os.path.join(inputs_folder, "excluded.txt")

        # Check and create Keywords.txt file
        if not os.path.exists(keywords_file):
            with open(keywords_file, 'w') as f:
                f.write("")  # Create an empty file
            # print(f"Created file: {keywords_file}")

        # Check and create excluded.txt file
        if not os.path.exists(excluded_file):
            with open(excluded_file, 'w') as f:
                f.write("")  # Create an empty file
            # print(f"Created file: {excluded_file}")
    def user_status(self):
        try:
            mac=activity_data.get_mac_address()    
            CMS_app=activity_data.fetch_app_data(1,mac)
            self.user_data = CMS_app.get('user', {})
            if self.user_data:
                return True
            else:
                # print("False")
                return False
        except:return  False 
    def read_keywords_from_file(self):
        try:
            with open('inputs/keywords.txt', 'r') as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "keywords.txt file not found.")
            return []

    def stop_scraping(self):
        if not self.scraping_running:
            return
        # self.update_button_state()
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, 'Stop Scraping', 'Are you sure you want to stop the scraping process?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.worker_thread.stop()
                self.worker_thread.wait()
                self.timer.stop()
                self.loading_modal.close()
        self.scraping_running = False

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Close Application', 'Are you sure you want to close the application?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()

        else:
            event.ignore()

    def update_status(self, message):
        QMessageBox.information(self, "Status Update", message)
        self.loading_modal.close()

    def update_scraped_data(self, count):
        self.result_count += count
        self.scraped_data_label.setText(f"Scraped data: {self.result_count}")

    
    def show_loading_modal(self):
        self.loading_modal = QDialog(self)
        self.loading_modal.setObjectName('loading_modal')
        self.loading_modal.setWindowTitle("Scraping")
        self.loading_modal.setFixedSize(300, 300)
        self.loading_modal.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowTitleHint)
        
        # # Center the loading modal
        parent_geometry = self.geometry()
        # print(parent_geometry)
        modal_geometry = self.loading_modal.geometry()

        center_x = (parent_geometry.center().x() - modal_geometry.width()) // 2 + 280
        center_y = (parent_geometry.center().y() - modal_geometry.height()) // 2 + 220
        self.loading_modal.move(center_x, center_y)

        modal_layout = QVBoxLayout()
        self.total_keywords_label = QLabel(f"Search Terms: {self.total_keywords}")
        self.time_label = QLabel(f"Start Time: {self.convert_Time_HMS(self.start_time)}")
        self.Elapsed = QLabel(f"Estimated Run Time: {self.convert_seconds_HMS(self.estimated_time)}")
        self.time_remaining_label = QLabel(self.format_time(self.estimated_time))
        self.Estimated_Finish_Time = QLabel(f"Estimated Finish Time: {self.add_seconds_to_current_time(self.estimated_time)}")

        modal_layout.addWidget(self.total_keywords_label)
        modal_layout.addWidget(self.time_label)
        modal_layout.addWidget(self.Elapsed)
        modal_layout.addWidget(self.time_remaining_label)
        modal_layout.addWidget(self.Estimated_Finish_Time)

        loading_label = QLabel()
        loading_movie = QMovie("res/loading.gif")
        loading_movie.setScaledSize(QSize(130, 100))
        loading_label.setMovie(loading_movie)
        loading_movie.start()

        modal_layout.addWidget(loading_label, alignment=Qt.AlignCenter)
        self.loading_modal.setLayout(modal_layout)
        self.loading_modal.exec_()

    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"Remaining Time: {hours:02}:{minutes:02}:{seconds:02}"
    def add_seconds_to_current_time(self, seconds):
            current_time = datetime.datetime.now()
            future_time = current_time + datetime.timedelta(seconds=seconds)
            
            # Format the future_time as h:m:s
            formatted_future_time = future_time.strftime("%H:%M:%S")
    
            return formatted_future_time
    def convert_seconds_HMS(self, seconds):
            duration = datetime.timedelta(seconds=seconds)
            # Extract hours, minutes, and seconds from the duration
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            # Format as h:m:s
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"
            return formatted_time
    def convert_Time_HMS(self, start_time):
            # future_time =  datetime.timedelta(seconds=seconds)
            # Format the future_time as h:m:s
            formatted_future_time = start_time.strftime("%H:%M:%S")
            return formatted_future_time
    def update_time(self):
        self.estimated_time -= 1
        self.time_remaining_label.setText(self.format_time(self.estimated_time))
        if self.estimated_time <= 0:
            self.timer.stop()
    # Function to calculate time spent
    def calculate_time_spent(self, start_time, end_time):   
        # Calculate time difference in seconds
        time_difference = (end_time - start_time)
        
       # Extract hours, minutes, and seconds from the time difference
        hours, remainder = divmod(time_difference.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format the time difference as h:m:s
        formatted_time_difference = f"{int(hours)}:{int(minutes)}:{int(seconds)}"
        
        return formatted_time_difference

    def download_data(self):
        filename = self.output_filename.text().strip()
        file_type = self.output_format.currentText()
        # result_list = searchEngine.get_result_list()
        result_list=self.worker_thread.results
        current_time=datetime.datetime.now().replace(microsecond=0)
        strtime=self.start_time
        appname=self.app_data.get('name')
        user_id=self.user_data.get('id')
        tkeywords=self.total_keywords

        spent_time=self.calculate_time_spent(strtime,current_time)
        res=activity_data.send_activity_data(appname,4, user_id, spent_time, strtime, current_time,tkeywords)
   
        if not self.output_folder:
            self.output_folder='outputs'
            
            
        if any(res is None for res in result_list):

            return False
        

        last_file = rearrange.rearrange_results(self.worker_thread.urls, result_list)
        if file_type == "CSV":
                file_name = f"{self.output_folder}/{filename}.csv"
                self.write_to_csv(file_name, last_file)

        elif file_type == "XLSX":
            file_name = f"{self.output_folder}/{filename}.xlsx"
            self.write_to_excel(file_name, last_file)
        searchEngine.resultList.clear()
        self.result_list=''  
        last_file=''  
        return True

    def write_to_csv(self, filename, result_list):
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Keyword","Title", "Link"])
            writer.writerows(result_list)
       
    def write_to_excel(self, filename, result_list):
   
        df = pd.DataFrame(result_list, columns=["Keyword","Title", "Link","Link1","Link2"])
        
        df.to_excel(filename,index=False)
 
    def refresh_app(self):
    # Clear excluded domains array
        self.excluded_domains.clear()

        # Re-import excluded domains from excluded.txt
        with open('inputs/excluded.txt', 'r') as excluded_file:
            self.excluded_domains.extend(line.strip() for line in excluded_file if line.strip())

        # Clear search term keywords array (urls)
        self.worker_thread.urls.clear()

        # Re-import keywords from keywords.txt
        with open('inputs/keywords.txt', 'r') as keywords_file:
            self.worker_thread.urls.extend(line.strip() for line in keywords_file if line.strip())

        # Optionally clear resultList or any other state variables if needed
        searchEngine.resultList.clear()
        self.result_list=''



def show_splash_screen(app, app_data):
    background_color = app_data.get('color_background', '#f0e6e7')
    splash = QWidget()
    splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    
    # Get screen resolution
    screen_resolution = QDesktopWidget().availableGeometry()
    screen_width = screen_resolution.width()
    screen_height = screen_resolution.height()
    
    # Calculate window size (70% of screen size)
    window_width = int(screen_width * 0.7)
    window_height = int(screen_height * 0.7)
    
    # Center the window on the screen
    splash.setGeometry(
        (screen_width - window_width) // 2,
        (screen_height - window_height) // 2,
        window_width,
        window_height
    )
    
    splash.setStyleSheet(f"background-color: {background_color}")  # Set background color
    
    layout = QVBoxLayout(splash)
    layout.setAlignment(Qt.AlignCenter)  # Center the layout
    
    splash_image = QLabel()
    splash_movie = QMovie("res/splash.gif")  # Add the path to your splash gif here
    splash_movie.setScaledSize(QSize(window_width, window_height))
    splash_movie.start()
    
    splash_image.setMovie(splash_movie)
    splash_image.setAlignment(Qt.AlignCenter)
    layout.addWidget(splash_image)
    
    splash.setLayout(layout)
    splash.show()
    
    return splash
def initialize_directories_and_files():
    
    # Define the folder paths
    inputs_folder = "inputs"
    outputs_folder = "outputs"

        
        

    # Check and create inputs folder
    if not os.path.exists(inputs_folder):
        os.makedirs(inputs_folder)
        # print(f"Created folder: {inputs_folder}")

    # Check and create outputs folder
    if not os.path.exists(outputs_folder):
        os.makedirs(outputs_folder)
        # print(f"Created folder: {outputs_folder}")

    # Define the file paths
    keywords_file = os.path.join(inputs_folder, "keywords.txt")
    excluded_file = os.path.join(inputs_folder, "excluded.txt")

    # Check and create Keywords.txt file
    if not os.path.exists(keywords_file):
        with open(keywords_file, 'w') as f:
            f.write("")  # Create an empty file
        # print(f"Created file: {keywords_file}")

    # Check and create excluded.txt file
    if not os.path.exists(excluded_file):
        with open(excluded_file, 'w') as f:
            f.write("")  # Create an empty file
        # print(f"Created file: {excluded_file}")
def run_application():
    project_id=1
    initialize_directories_and_files()
    mac=activity_data.get_mac_address()    
    CMS_app=activity_data.fetch_app_data(project_id,mac)
    app_data = CMS_app.get('data', {})
    # print(CMS_app)
    # print(mac)
    
    app = QApplication(sys.argv)
    app.setStyleSheet(generate_dynamic_qss(app_data))
    splash = show_splash_screen(app,app_data)  
    
      # 5000 milliseconds = 5 seconds    
    
    main_window = MainWindow(app_data)
    QTimer.singleShot(5000, splash.close)
    QTimer.singleShot(5000, lambda: main_window.showNormal())
    
    # window.showMaximized()
    sys.exit(app.exec_())



import platform
import subprocess
import hashlib

# Predefined list of allowed device IDs

def get_device_id():
    os_name = platform.system()
    
    if os_name == "Windows":
        return get_windows_device_id()
    elif os_name == "Darwin":
        return get_mac_device_id()
    elif os_name == "Linux":
        return get_linux_device_id()
    else:
        raise Exception(f"Unsupported OS: {os_name}")

def get_windows_device_id():
    try:
        # Get BIOS serial number
        bios_serial = subprocess.check_output('wmic bios get serialnumber', shell=True).decode().split('\n')[1].strip()

        # Get motherboard serial number
        motherboard_serial = subprocess.check_output('wmic baseboard get serialnumber', shell=True).decode().split('\n')[1].strip()

        # Get processor ID
        processor_id = subprocess.check_output('wmic cpu get processorid', shell=True).decode().split('\n')[1].strip()

        # Combine these to create a unique identifier
        combined_id = bios_serial + motherboard_serial + processor_id

        # Hash the combined ID to get a unique device ID
        device_id = hashlib.sha256(combined_id.encode()).hexdigest()
        return device_id
    except Exception as e:
        raise Exception(f"Failed to retrieve device ID on Windows: {e}")

def get_mac_device_id():
    try:
        # Get system serial number
        serial_number = subprocess.check_output("system_profiler SPHardwareDataType | awk '/Serial/ {print $4}'", shell=True).decode().strip()

        # Get hardware UUID
        hardware_uuid = subprocess.check_output("system_profiler SPHardwareDataType | awk '/UUID/ {print $3}'", shell=True).decode().strip()

        # Combine these to create a unique identifier
        combined_id = serial_number + hardware_uuid

        # Hash the combined ID to get a unique device ID
        device_id = hashlib.sha256(combined_id.encode()).hexdigest()
        return device_id
    except Exception as e:
        raise Exception(f"Failed to retrieve device ID on macOS: {e}")

def get_linux_device_id():
    try:
        # Get the machine-id (unique to each installation)
        machine_id = subprocess.check_output("cat /etc/machine-id", shell=True).decode().strip()

        # Get system UUID
        system_uuid = subprocess.check_output("cat /sys/class/dmi/id/product_uuid", shell=True).decode().strip()

        # Combine these to create a unique identifier
        combined_id = machine_id + system_uuid

        # Hash the combined ID to get a unique device ID
        device_id = hashlib.sha256(combined_id.encode()).hexdigest()
        return device_id
    except Exception as e:
        raise Exception(f"Failed to retrieve device ID on Linux: {e}")

class RegisterWindow(QMainWindow):
    def __init__(self, app_data):
        super().__init__()
        self.app_data = app_data
        self.setWindowTitle("Register")
        self.setFixedSize(400, 300)

        # Center the window on the screen
        screen_resolution = QDesktopWidget().availableGeometry()
        self.setGeometry(
            (screen_resolution.width() - 400) // 2,
            (screen_resolution.height() - 300) // 2,
            400,
            300
        )

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)  # Adjust the margins around the layout
        main_layout.setSpacing(2)  # Reduce the space between widgets in the layout

        # Form layout for registration fields
        form_layout = QFormLayout()
        form_layout.setSpacing(2)  # Adjust the spacing between form elements

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        form_layout.addRow(QLabel("Email:"), self.email_input)

        # Add form layout to main layout
        main_layout.addLayout(form_layout)

        # Notification label (initially hidden)
        self.notification = QLabel("")
        self.notification.setAlignment(Qt.AlignCenter)
        self.notification.setStyleSheet("color: red;")
        self.notification.setFixedHeight(30)  # Reduce the height of the notification label
        self.notification.hide()  # Hidden until a notification is shown
        main_layout.addWidget(self.notification)

        # Register and cancel buttons
        register_button = QPushButton("Register")
        register_button.clicked.connect(self.register_user)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Adjust the space between buttons
        button_layout.addWidget(register_button)
        button_layout.addWidget(cancel_button)

        # Add buttons to the main layout
        main_layout.addLayout(button_layout)

        # Set main widget and layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Apply custom styles (QSS)
        self.setStyleSheet(generate_dynamic_qss(app_data))

    def register_user(self):
        email = self.email_input.text().strip()

        if not email:
            self.show_notification("Please enter an email address.")
            return
        global is_register
        device_id = get_device_id()
        # Construct the API URL
        api_url = f"https://autofyn.com/Authentication_app/device_exist.php/{email}/{device_id}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                response_data = response.json()  # Get the JSON response
                status = response_data.get("status", "Unknown status")
                message = response_data.get("message", "No message provided")  # Assuming the API returns a message
                is_register = (status == "success")
                
                # Show the status and message from the response
                self.show_notification(f"Registration status: {status}\nMessage: {message}", success=is_register)
            else:
                self.show_notification("Failed to reach the server.")
        except requests.RequestException as e:
            self.show_notification(f"Error: {str(e)}")

    def show_notification(self, message, success=False):
        # Display a message to the user
        self.notification.setText(message)
        self.notification.setStyleSheet("color: green;" if success else "color: red;")
        self.notification.show()



if __name__ == "__main__":
    app = QApplication([])

    mac = activity_data.get_mac_address()
    mac = get_device_id()
    # print(mac)
    CMS_app = activity_data.fetch_app_data(1, mac)
    user_data = CMS_app.get('user', {})

    if not user_data:
        app_data = {
            'text_2': 'Footer Text',
            'color_background': '#f0e6e7',
            'color_text': '#000000',
            'color_button_text_hover': '#7e221b',
            'color_input_border': '#000000',
            'color_button': '#000000',
            'color_button_text': '#FFFFFF'
        }
        register = RegisterWindow(app_data)
        register.show()
        result = app.exec_()

        if is_register:
            latest_version_info = check_for_updates()
            # print(latest_version_info)
            if latest_version_info:
                download_url = "https://autofyn.com/download_exe/index.php"
                reply = QMessageBox.question(app.activeWindow(), "Update Available", "A new version is available. Do you want to update now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    webbrowser.open(download_url)
            initialize_directories_and_files()
            run_application()
        # QMessageBox.warning(None, "Danger", "Please contact the admin. You are not eligible to use this app.")
    else:
        latest_version_info = check_for_updates()
        # print(latest_version_info)
        if latest_version_info:
            download_url = "https://autofyn.com/download_exe/index.php"
            reply = QMessageBox.question(app.activeWindow(), "Update Available", "A new version is available. Do you want to update now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                webbrowser.open(download_url)
        initialize_directories_and_files()
        run_application()    
    











