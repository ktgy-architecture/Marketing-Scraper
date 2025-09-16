import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

BASE = "https://ktgy.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KTGY Project Scraper/1.0; +https://ktgy.com)"
}

session = requests.Session()
session.headers.update(HEADERS)
options = Options()
# options.add_argument("--headless")
options.add_argument('–-window-size=1920,1080')
browser = webdriver.Chrome(service=ChromeService(executable_path=r"./chromedriver.exe"), options=options)


def fetch_page_data(url):
    browser.get(url)
    click_count = 0
    while True:
        try:
            time.sleep(2.5)
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(5)
            button = WebDriverWait(browser, 10).until(EC.element_to_be_clickable(browser.find_element(By.XPATH, "//*[contains(text(), 'VIEW MORE')]")))
            button.click()
            click_count += 1
            print(f"[DEBUG]: Click {click_count}!")
        except NoSuchElementException:
            print("[DEBUG]: No more clicking.")
            break
        except Exception as e:
            print(e)
            break
    return browser.page_source


def discover_project_urls() -> list[str]:
    urls = []
    api = f"{BASE}/all-work/?view_type=list"
    print(f"Fetching page {api}")
    data = fetch_page_data(api)

    soup = BeautifulSoup(data, "html.parser")
    for a in soup.select("div.people_filter__person"):
        href = a.select("a")[0].get("href")
        matcher = "https:/Work/"
        if href and href.startswith(matcher):
            urls.append(urljoin(BASE, href))
    print(f"Found {len(urls)} URLS: {urls[-5:]}, unique-count: {len(set(urls))}")
    return sorted(set(urls))


def parse_project(url: str) -> dict:
    r = session.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    top_block = soup.find("section", attrs={"class": "project-info"})
    name = top_block.find(re.compile("^h[1-6]$"), attrs={"class": "project-info__title"}).text
    location = top_block.find(re.compile("^h[1-6]$"), attrs={"class": "project-info__location"}).text
    client = top_block.find("p", attrs={"class": "body-copy"}).text

    cls_block = top_block.find("div", attrs={"class": "project-info__tags"})
    tags = cls_block.find_all("li")
    classifications = [tag.text for tag in tags]

    description_block = soup.find("section", attrs={"class": "module copy_block copy_block-v1"})
    description = description_block.find_all("p")
    description = "".join([d_block.text for d_block in description])

    facts_block = soup.find("section", attrs={"class": "module callout_expandable"})
    if facts_block is not None:
        facts_subset = facts_block.find("div", attrs={"class": "callout_expandable__boxes row"})
        fact_keys = facts_subset.find_all("p")
        fact_vals = facts_subset.find_all(re.compile("^h[1-6]$"))
        facts = {k.text: v.text for k, v in zip(fact_keys, fact_vals)}
    else:
        facts = {}

    data = {
        "Project Name": name,
        "Location": location,
        "Client/Developer": client,
        "Classifications": classifications,
        "Project URL": url,
        "Description": description,
        "Facts": facts,
    }
    return data


def main():
    print("Discovering project URLs...")
    urls = discover_project_urls()
    print(f"Found {len(urls)} projects")

    rows = []
    for url in tqdm(urls, unit="proj"):
        try:
            rows.append(parse_project(url))
        except Exception as e:
            print(f"Project: {url}:", e)

    df = pd.DataFrame(rows)
    df.to_csv("./data/ktgy_projects.csv", index=False)
    df.to_excel("./data/ktgy_projects.xlsx", index=False)
    print("Saved ktgy_projects.csv and ktgy_projects.xlsx")


if __name__ == "__main__":
    main()
