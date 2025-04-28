from os import getenv
from dotenv import load_dotenv
import requests, urllib3
from json import loads
import csv
from time import time

import tkinter as tk
from tkinter import filedialog, ttk

from selenium import webdriver
from selenium import common
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def open_csv():
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file=file_path, mode='r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)
        return data


class App():
    def __init__(self, background_update_frequancy: int=20):
        self.logged_in = False
        self.browser = None 
        self.errors = []
        self.data_lines = []
        self.session_cookies = {}
        self.out_dir = ''
        self.token = ''
        self.api_token = ''
        self.last_update=time()
        self.background_update_frequancy = background_update_frequancy


        load_dotenv()
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #prevent warning for unsecure url in logs

        #Tkinter Window
        self.root = tk.Tk()
        self.root.title("ADL generator")
        # self.root.geometry("500x200")  # Optional: fixed starting size

        # Main container
        w = ttk.Frame(self.root, padding="10 10 10 10")
        w.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Progress bar container frame with a custom style
        progress_frame = ttk.Frame(w, style="Progress.TFrame")
        progress_frame.grid(column=0, columnspan=4, row=2, sticky="ew", padx=5, pady=(5, 10))

        # Actual progress bar
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill="x")

        # Percentage label over the progress bar with a custom style
        self.progress_label = ttk.Label(progress_frame, text="0%", anchor="center", style="Progress.TLabel")
        self.progress_label.place(relx=0.5, rely=0.5, anchor="center")

        # Action buttons
        button_frame = ttk.Frame(w)
        button_frame.grid(column=0, columnspan=4, row=3, pady=10)

        for i, (label, cmd) in enumerate([("annuler", lambda: self.root.destroy()), ("démarer", self.start)]):
            btn = ttk.Button(button_frame, text=label, width=10, command=cmd)
            btn.grid(row=0, column=i, padx=10)

        w.columnconfigure(0, weight=1, uniform="equal")
        w.columnconfigure(2, weight=1, uniform="equal")
        w.columnconfigure(3, weight=0)
        
        w.rowconfigure(0, weight=0)
        w.rowconfigure(2, weight=0)
        w.rowconfigure(3, weight=0)

        self.root.mainloop()


    def start(self):
        #login M3
        try:
            self.login()
        except common.exceptions.NoSuchWindowException:
            return
        self.get_cookies()
        self.browser.close()

        #M3 open console
        url = "https://m3pr1.scabel.lan:31010/mne/servlet/MvxMCSvt"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"}
        params1 = {
            "CMDTP": "LOGON",
            "ROLES": "",
            "WPF": "TRUE",
            "EXL": "TRUE",
            "CTT": "TRUE",
            "CSTMODE": "2",
            "CLIENT": "WebUI",
            "SOURCE": "H5",
            "inforCurrentLocale": "fr-FR",
            "inforTimeZone": "(UTC+01:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna",
            "MINGLE": "TRUE"
            }
        params2 = {
            "CMDTP": "RUN",
            "CMDVAL": "ZZS320",
            "BMREQ": "",
            "SID": ""
            }
        with requests.Session() as session:
            session.cookies.update(self.session_cookies)
            response = session.post(url, headers=headers, stream=True, verify=False, json=params1)
            #TODO get SID from response xml to params2
            response = session.post(url, headers=headers, stream=True, verify=False, json=params2)

        input_data = open_csv()
        self.progress.config(maximum=len(input_data))

        for line in input_data:
            self.progress_tick()
            if len(line) == 0:
                continue
            self.progress_label.config(text=f"id - ")

            data = self.querry(order=line[0], supplier=line[1])
            if data is None:
                self.errors.append(id)
            else:
                self.data_lines.append(data)

        if len(self.errors) > 0:
            with open("errors.txt", "w") as file:
                file.write(str(self.errors))

        self.root.destroy()


    def login(self):
        self.browser = webdriver.Firefox()
        self.browser.get("https://portailm3.scabel.lan:9543/ca/")
        wait = WebDriverWait(self.browser, 10)

        nameInput = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='userNameInput']")))
        nameInput.send_keys(getenv("M3USER"))

        passwordInput = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='passwordInput']")))
        passwordInput.send_keys(getenv("M3PSWD"))
        passwordInput.send_keys(Keys.RETURN)

        wait.until(EC.url_contains("ca/"))
        self.logged_in = True


    def querry(self, supplier, order, IID):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"}
        url1 = f"https://m3pr1.scabel.lan:31010/mne/servlet/MvxMCSvt"
        params = {
            "IID": IID,
            "WFSUNO": supplier,
            "WFORNO": order,
            "WTORNO": order,
            "WFSINO": "",
            "WFINYR": "",
            "WTSINO": "",
            "WTINYR": "",
            "WFTX30": "",
            "WFITNO": "",
            "WTITNO": "",
            "WFRLDT": "",
            "WTRLDT": "",
            "WFCLAD": "",
            "WTCLAD": "",
            "WEXCLU": "on",
            "FCS": "WTINYR",
            "CMDTP": "KEY",
            "CMDVAL": "ENTER"
        }
        with requests.Session() as session:
            session.cookies.update(self.session_cookies)
            response = session.post(url1, headers=headers, stream=True, verify=False, json=params)
            if response.status_code == 200:
                print(response.content)
                return "ok"
            else:
                print(f"Failed to download {id}: HTTP {response.status_code}")


    def progress_tick(self):
        self.progress["value"] += 1
        now = time()
        if now-self.last_update > 1/self.background_update_frequancy:
            self.root.update()


    def get_session_token(self):
        return loads(self.browser.execute_script("return localStorage.getItem('jwtSession');"))["access_token"]
    

    def get_api_token(self):
        return self.browser.execute_script("return localStorage.getItem('ngapiToken');")


    def get_session_storage(self):
        return self.browser.execute_script("var items = {}; for (var i = 0; i < sessionStorage.length; i++) { var key = sessionStorage.key(i); items[key] = sessionStorage.getItem(key); } return items;")


    def get_cookies(self):
        for cookie in self.browser.get_cookies():
            self.session_cookies[cookie['name']] = cookie['value']


if __name__ == "__main__":
    App()




# https://m3pr1.scabel.lan:31010/mne/servlet/MvxMCSvt
# {
#   "CMDTP": "RUN",
#   "CMDVAL": "ZZS320",
#   "BMREQ": "",
#   "SID": "413f2e5bc68429a5a0364d1b43e2f555"
# }