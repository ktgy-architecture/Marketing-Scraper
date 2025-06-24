import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

BASE = "https://ktgy.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KTGY Project Scraper/1.0; +https://ktgy.com)"
}

session = requests.Session()
session.headers.update(HEADERS)


def discover_project_urls() -> list[str]:
    urls = []
    page = 1
    count_last = 0
    while True:
        print(f"Fetching page {page}")
        api = f"{BASE}/all-work/?page-num={page}&view_type=list"
        r = session.get(api, timeout=30)
        print(f"Got status code {r.status_code} for page {page}")

        data = r.text
        soup = BeautifulSoup(data, "html.parser")
        for a in soup.select("div.people_filter__person"):
            href = a.select("a")[0].get("href")
            if href and href.startswith(f"{BASE}/Work/"):
                urls.append(urljoin(BASE, href))
        print(f"Found {len(urls)} URLS: {urls[-5:]}")
        page += 1

        if count_last == len(urls):
            break
        count_last = len(urls)
        time.sleep(0.25)
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
