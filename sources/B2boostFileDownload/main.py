from os import getenv
from dotenv import load_dotenv
import requests, urllib3
from json import loads
import icon_b64

import tkinter as tk
from tkinter import filedialog, ttk

from selenium import webdriver
from selenium import common
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class App():
    def __init__(self):
        self.logged_in = False
        self.browser = None 
        self.errors = []
        self.data_lines = []
        self.session_cookies = {}
        self.out_dir = ''
        self.token = ''
        self.api_token = ''

        load_dotenv()
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #prevent warning for unsecure url in logs

        #Tkinter Window
        self.root = tk.Tk()
        self.root.title("Téléchargeur de factures B2boost")
        self.root.geometry("500x300")  # Optional: fixed starting size
        self.root.wm_iconphoto(True, icon_b64.get_icon())

        # Main container
        w = ttk.Frame(self.root, padding="10 10 10 10")
        w.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Output label + entry + browse
        ttk.Label(w, text="Sortie:").grid(column=0, row=0, sticky=tk.E, padx=5, pady=5)

        self.path = tk.StringVar()
        path_entry = ttk.Entry(w, textvariable=self.path, width=40)
        path_entry.grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        browse_btn = ttk.Button(w, text="parcourir", command=self.browse)
        browse_btn.grid(column=2, row=0, sticky=tk.W, padx=5, pady=5)

        # Text box with scrollbar
        self.data = tk.Text(w, height=8, wrap="word")
        self.data.grid(column=0, columnspan=3, row=1, sticky="nsew", padx=5, pady=5)

        scrollbar = ttk.Scrollbar(w, orient="vertical", command=self.data.yview)
        scrollbar.grid(row=1, column=3, sticky="ns", pady=5)
        self.data.config(yscrollcommand=scrollbar.set)

        # Progress bar container frame with a custom style
        progress_frame = ttk.Frame(w, style="Progress.TFrame")
        progress_frame.grid(column=0, columnspan=4, row=2, sticky="ew", padx=5, pady=(5, 10))

        # Actual progress bar
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill="x")

        # Percentage label over the progress bar with a custom style
        self.progress_label = ttk.Label(progress_frame, text="", anchor="center", style="Progress.TLabel")
        self.progress_label.place(relx=0.5, rely=0.5, anchor="center")

        # Action buttons
        button_frame = ttk.Frame(w)
        button_frame.grid(column=0, columnspan=4, row=3, pady=10)

        for i, (label, cmd) in enumerate([("annuler", lambda: self.root.destroy()), ("démarer", self.start)]):
            btn = ttk.Button(button_frame, text=label, width=10, command=cmd)
            btn.grid(row=0, column=i, padx=10)

        w.columnconfigure(0, weight=1, uniform="equal")
        w.columnconfigure(1, weight=3, uniform="equal")
        w.columnconfigure(2, weight=1, uniform="equal")
        w.columnconfigure(3, weight=0)
        
        w.rowconfigure(0, weight=0)
        w.rowconfigure(1, weight=3)
        w.rowconfigure(2, weight=0)
        w.rowconfigure(3, weight=0)

        self.root.mainloop()


    def start(self):
        # login via selenium & get cookies
        try:
            self.login()
        except common.exceptions.NoSuchWindowException:
            return
        self.get_cookies()
        self.token = self.get_session_token()
        self.api_token = self.get_api_token()
        self.browser.close()

        # get relevent data
        self.out_dir = self.path.get()
        ids = self.data.get(1.0, "end-1c").strip().split("\n")
        self.progress.config(maximum=len(ids))

        # run downloads
        for id in ids:
            self.progress_label.config(text=f"id - ")
            if len(id.strip()) == 0:
                continue
            data = self.querry(id.strip())
            if data is None:
                self.errors.append(id)
            else:
                self.data_lines.append(data)
            self.progress_tick()

        #log output
        if len(self.errors) > 0:
            with open("errors.txt", "w") as file:
                file.write(str(self.errors))

        if len(self.data_lines) > 0:
            with open("data.json", "w") as file:
                file.write(str(self.data_lines))
        self.root.destroy()


    def browse(self):
        path = filedialog.askdirectory()
        self.path.set(path)


    def login(self):
        self.browser = webdriver.Firefox()
        self.browser.get("https://eurelec.multi.b2boost.io/home")
        user = getenv("B2BOOSTUSER")
        pswd = getenv("B2BOOSTPSWD")

        #allow user to manually login if no .env values can be found
        wait = WebDriverWait(self.browser, 300)
        if not user is None and not pswd is None:
            wait = WebDriverWait(self.browser, 10)
            nameInput = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='username']")))
            nameInput.send_keys(user)

            passwordInput = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='password']")))
            passwordInput.send_keys(pswd)
            passwordInput.send_keys(Keys.RETURN)

        wait.until(EC.url_contains("documents"))
        self.logged_in = True


    def querry(self, id):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            'Authorization': f'Bearer {self.token}',
            'X-Authentication': self.api_token
        }
        url1 = f"https://eurelec.multi.b2boost.io/api/invoices/search"
        params = {"sort":[{"documentDate":{"order":"desc"}}],"from":0,"size":10,"query":{"bool":{"must":[{"multi_match":{"query":id,"operator":"AND","fuzziness":2,"boost":0,"fields":["supplierName.analyzed","msgType.analyzed","supplierRef.analyzed","ref.analyzed","buyerOrderRef.analyzed"],"type":"cross_fields"}},{"match":{"flowDirection":"OUTBOUND"}}],"should":[{"multi_match":{"query":id,"fields":["supplierName.analyzed","msgType.analyzed","supplierRef.analyzed","ref.analyzed","buyerOrderRef.analyzed"],"boost":1}}]}},"_source":{"exclude":[]}}
        with requests.Session() as session:
            session.cookies.update(self.session_cookies)
            response1 = session.post(url1, headers=headers, stream=True, verify=False, json=params)
            if response1.json()["total"] == 0:
                print(f"Failed to download {id}: Not Found")
                return
            b2b_id = response1.json()["hits"][0]["_id"]
            url2 = f"https://eurelec.multi.b2boost.io/api/messages/{b2b_id}/attachments/type/outbound.readable.message"
            response2 = session.get(url2, headers=headers, stream=True, verify=False)
            if response2.status_code == 200:
                filename = f"{self.out_dir}/{response2.headers["X-attachment-name"]}"
                with open(filename, "wb") as f:
                    for chunk in response2.iter_content(1024):
                        f.write(chunk)
                print(f"Downloaded {filename}")
                return "ok"
            else:
                print(f"Failed to download {id}: HTTP {response2.status_code}")


    def progress_tick(self):
        pass


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