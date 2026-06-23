"""
NECC Egg Price Extractor
Source: https://www.e2necc.com/home/eggprice

The site uses JavaScript to render the table, so we use Selenium
with a headless Chrome browser to extract the data.

Output: CSV  -> necc_egg_price_<YYYYMMDD>.csv
        JSON -> necc_egg_price_<YYYYMMDD>.json

Usage:
    pip install selenium pandas webdriver-manager
    python necc_egg_price_extractor.py
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL   = "https://www.e2necc.com/home/eggprice"
TODAY = datetime.today().strftime("%Y%m%d")
OUTDIR = Path("output")
OUTDIR.mkdir(exist_ok=True)


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def extract_table(driver):
    print(f"[INFO] Loading {URL} ...")
    driver.get(URL)

    # Wait for table to appear
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )
    time.sleep(3)  # let JS fully render

    tables = driver.find_elements(By.TAG_NAME, "table")
    print(f"[INFO] Found {len(tables)} table(s) on page.")

    all_dfs = []
    for i, table in enumerate(tables):
        html = table.get_attribute("outerHTML")
        try:
            dfs = pd.read_html(html)
            for df in dfs:
                if not df.empty:
                    all_dfs.append(df)
                    print(f"[OK] Table {i+1}: {len(df)} rows x {len(df.columns)} cols")
        except Exception as e:
            print(f"[WARN] Could not parse table {i+1}: {e}")

    return all_dfs


def save_outputs(df: pd.DataFrame):
    csv_path  = OUTDIR / f"necc_egg_price_{TODAY}.csv"
    json_path = OUTDIR / f"necc_egg_price_{TODAY}.json"

    df.to_csv(csv_path, index=False)
    records = df.to_dict(orient="records")
    json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))

    print(f"\n[OK] Saved {len(df)} rows:")
    print(f"   CSV  -> {csv_path}")
    print(f"   JSON -> {json_path}")


def main():
    driver = None
    try:
        driver = get_driver()
        dfs = extract_table(driver)

        if not dfs:
            print("[ERROR] No tables found.")
            return

        # Use the largest table (main price table)
        df = max(dfs, key=len)

        # Add extraction date
        df.insert(0, "extracted_date", datetime.today().strftime("%Y-%m-%d"))

        print("\n[PREVIEW] First 5 rows:")
        print(df.head().to_string())

        save_outputs(df)

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
