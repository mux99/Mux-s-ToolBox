from os import getenv
from dotenv import load_dotenv
import requests, urllib3

import tkinter as tk
from time import sleep

from selenium import webdriver
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
        self.tokena = ''

        load_dotenv()
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #prevent warning for unsecure url in logs

        #Tkinter Window
        self.window = tk.Tk()
        self.window.title("Edicom Invoice Check")
        self.textInput = tk.Text(self.window, height=5, width=30)
        self.textInput.pack()
        tk.Button(self.window, text="check", command=self.start).pack()
        self.window.mainloop()


    def start(self):
        self.login()
        self.get_cookies()
        self.tokena = self.get_session_storage()['tokena']
        self.browser.close()

        for id in self.textInput.get(1.0, "end-1c").strip().split("\n"):
            if len(id.strip()) == 0:
                continue
            data = self.querry(id.strip())
            if data is None:
                self.errors.append(id)
            else:
                self.data_lines.append(data)

        if len(self.errors) > 0:
            with open("errors.txt", "w") as file:
                file.write(str(self.errors))

        if len(self.data_lines) > 0:
            with open("data.json", "w") as file:
                file.write(str(self.data_lines))
        self.window.destroy()


    def login(self):
        self.browser = webdriver.Firefox()
        self.browser.get("https://clients.edicomgroup.com/ediwin-viewer-extended-access.htm")
        wait = WebDriverWait(self.browser, 10)

        nameInput = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='usuario']")))
        nameInput.send_keys(getenv("EDICOMUSER"))

        passwordInput = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='password']")))
        passwordInput.send_keys(getenv("EDICOMPSWD"))
        passwordInput.send_keys(Keys.RETURN)

        sleep(2)
        self.logged_in = True


    def querry(self, id):
        url = f"https://ediwin.edicomgroup.com/api/documents/getDocumentsHeaders?page=0&size=1000&folder=463389"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "tokena": self.tokena,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "sec-GPC": "1",
            "DNT": '1'
        }
        params = {"filter":{"filterCriteria":{"children":[{"children":[{"children":[],"criteria":{"v1":"IDEXTERNO","op":"LIKE","v2":f"%{id}%"},"union":"AND"},{"children":[],"criteria":{"v1":"FORMATO","op":"=","v2":"XML"},"union":None}],"criteria":None,"union":None}],"criteria":None,"union":None},"orderBy":"FECHACAMBIOESTADO DESC","groupBy":None,"to":"","from":"2024-04-07T22:00:00.000Z"}}
        out = None
        with requests.Session() as session:
            session.cookies.update(self.session_cookies)
            response = session.post(url, headers=headers, stream=True, verify=False, json=params)
            if response.status_code == 200 and response.json()["total"] != 0:
                out=[
                    response.json()["data"][0]["IDEXTERNO"],
                    response.json()["data"][0]["REFERENCIA"],
                    response.json()["data"][0]["FIRMADO"],
                    response.json()["data"][0]["LASTUPDATE"]]
            else:
                print(response)
        return out


    def get_session_storage(self):
        return self.browser.execute_script("var items = {}; for (var i = 0; i < sessionStorage.length; i++) { var key = sessionStorage.key(i); items[key] = sessionStorage.getItem(key); } return items;")


    def get_cookies(self):
        for cookie in self.browser.get_cookies():
            self.session_cookies[cookie['name']] = cookie['value']


if __name__ == "__main__":
    App()