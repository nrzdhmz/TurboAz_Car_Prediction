import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import json

BASE_URL = "https://turbo.az"
START_URL = "https://turbo.az/autos?q%5Bavailability_status%5D=&q%5Bbarter%5D=0&q%5Bcrashed%5D=1&q%5Bcurrency%5D=azn&q%5Bengine_volume_from%5D=&q%5Bengine_volume_to%5D=&q%5Bfor_spare_parts%5D=0&q%5Bloan%5D=0&q%5Bmake%5D%5B%5D=&q%5Bmileage_from%5D=&q%5Bmileage_to%5D=&q%5Bonly_shops%5D=&q%5Bpainted%5D=1&q%5Bpower_from%5D=&q%5Bpower_to%5D=&q%5Bprice_from%5D=&q%5Bprice_to%5D=&q%5Bsort%5D=&q%5Bused%5D=&q%5Byear_from%5D=&q%5Byear_to%5D="

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/116.0.0.0 Safari/537.36"
}

CHECKPOINT_FILE = "checkpoint.json"
CSV_FILE = "data/cars.csv"


def get_product_links(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    product_divs = soup.find_all("div", class_="products-i")
    links = [BASE_URL + div.find("a", class_="products-i__link")["href"]
            for div in product_divs if div.find("a", class_="products-i__link")]

    next_span = soup.find("span", class_="next")
    next_link = None
    if next_span and next_span.find("a"):
        next_link = BASE_URL + next_span.find("a")["href"]

    return links, next_link


def scrape_product(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    properties = {"url": url}

    for div in soup.find_all("div", class_="product-properties__i"):
        label_tag = div.find("label", class_="product-properties__i-name")
        value_tag = div.find("span", class_="product-properties__i-value")

        if not label_tag or not value_tag:
            continue

        label = label_tag.get_text(strip=True)
        value = value_tag.find("a").get_text(strip=True) if value_tag.find("a") else value_tag.get_text(strip=True)
        properties[label] = value

    price_tag = soup.find("div", class_="product-price__i")
    if price_tag:
        properties["price"] = price_tag.get_text(strip=True)

    return properties



def save_to_csv(filename, cars, headers_csv):
    """Append cars to CSV file, expand headers if needed"""
    all_keys = set(headers_csv)
    for car in cars:
        all_keys.update(car.keys())
    all_keys = list(all_keys)

    if set(all_keys) != set(headers_csv) and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            writer.writerows(rows)
        headers_csv = all_keys

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers_csv)
        for car in cars:
            writer.writerow(car)

    return headers_csv


def save_checkpoint(page, next_url, headers_csv):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"page": page, "next_url": next_url, "headers": headers_csv}, f)


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    checkpoint = load_checkpoint()
    if checkpoint:
        page = checkpoint["page"]
        current_url = checkpoint["next_url"]
        headers_csv = checkpoint["headers"]
        print(f"Resuming from page {page}, URL: {current_url}")
    else:
        page = 1
        current_url = START_URL
        headers_csv = ["url"]
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers_csv)
                writer.writeheader()

    while current_url:
        print(f"\nScraping page {page}: {current_url}")
        links, next_url = get_product_links(current_url)
        print(f"  Found {len(links)} product links")

        page_cars = []
        for link in links:
            print("   → Scraping:", link)
            try:
                data = scrape_product(link)
                page_cars.append(data)
                time.sleep(1)
            except Exception as e:
                print("   ! Error scraping:", link, e)

        headers_csv = save_to_csv(CSV_FILE, page_cars, headers_csv)
        save_checkpoint(page, next_url, headers_csv)
        print(f" Saved {len(page_cars)} cars from page {page}")

        current_url = next_url
        page += 1
        time.sleep(2)

    print("\n Scraping finished. All cars saved progressively in cars.csv")
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)  
