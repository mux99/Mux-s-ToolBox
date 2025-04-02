from selenium import webdriver
from os import getenv
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk
from time import sleep
import requests, urllib3

from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

options = Options()
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.dir", "C:/Users/maxime.dourov/Downloads")
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf,application/octet-stream,application/x-msdownload")
options.set_preference("pdfjs.disabled", True)
options.set_preference("browser.download.alwaysOpenInSystemViewerContextMenuItem", False)
options.enable_downloads = True

def login():
    global logged_in
    browser.get("https://portailm3.scabel.lan:9543/ca/")
    sleep(1)
    if "Connexion" in browser.title:
        print("Logging in...")
        user = getenv("M3USER")
        password = getenv("M3PSWD")
        nameInput = browser.find_element(By.XPATH, "//input[@id='userNameInput']")
        passwordInput = browser.find_element(By.XPATH, "//input[@id='passwordInput']")
        nameInput.send_keys(user)
        passwordInput.send_keys(password)
        passwordInput.send_keys(Keys.RETURN)
        sleep(2)
        logged_in = True
        print("Login successful.")
    else:
        logged_in = True

def get_cookies_from_selenium():
    cookies = browser.get_cookies()
    session_cookies = {}
    for cookie in cookies:
        session_cookies[cookie['name']] = cookie['value']
    return session_cookies

def downloadFile(fileID="0", type="ADL"):
    url = ''
    match type:
        case "ADL":
            url = f"https://portailm3.scabel.lan:9543/ca/api/items/search/item/resource/stream?$query=/ADL[@CLAN=%22{fileID.zfill(10)}%22]"
        case "Fact Vente":
            url = f"https://portailm3.scabel.lan:9543/ca/api/items/search/item/resource/stream?$query=/Facture_SCA[@IVNO=%22{fileID}%22]"
        case "Fact Achat":
            url = f"https://portailm3.scabel.lan:9543/ca/api/items/search/item/resource/stream?$query=/Facture_Interco[@CINO=%22{fileID}%22]"

    session_cookies = get_cookies_from_selenium()

    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    with requests.Session() as session:
        session.cookies.update(session_cookies)
        response = session.get(url, headers=headers, stream=True, verify=False)
        print(response)
        if response.status_code == 200:
            filename = f"out/{fileID}.pdf"
            with open(filename, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded {filename}")
        else:
            print(f"Failed to download {fileID}: HTTP {response.status_code}")

def start():
    if not 'selection' in globals():
        return()
    global browser
    browser = webdriver.Firefox(options=options) 
    login()
    for id in textInput.get(1.0, "end-1c").strip().split("\n"):
        downloadFile(id.strip(), selection)

def select(event):
    global selection
    selection = dropDown.get()

if __name__ == '__main__':
    load_dotenv()

    w = tk.Tk()
    w.title("Mass Downloader Options")
    dropDown = ttk.Combobox(w, values=["ADL","Fact Vente","Fact Achat"])
    dropDown.pack(pady=5)
    dropDown.set("select a type...")
    dropDown.bind("<<ComboboxSelected>>", select)
    textInput = tk.Text(w, height=5, width=30)
    textInput.pack()
    start = tk.Button(w, text="download", command=start)
    start.pack()
    w.mainloop()
    exit()
