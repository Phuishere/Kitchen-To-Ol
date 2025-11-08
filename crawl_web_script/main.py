'''
To run this:
python crawl_web_script/main.py
'''

import os
import time
import io
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException
)

# Configuration
BASE = "E:/projects/_full_fledge/Kitchen-Tools-Project"
DOWNLOAD_DIR = os.path.join(BASE, "resources", "crawled")
CHROME_DRIVER_PATH = "E:/projects/_full_fledge/Kitchen-Tools-Project/resources/chromedriver-win64/chromedriver.exe"

SEARCH_URL = ("https://www.google.com/search?"
              "q={query}&tbm=isch") # basic Google Images query url

MAX_IMAGES = 400
SCROLL_PAUSE = 1.0 # seconds
IMAGE_URLS = set()

# Setup webdriver
service = Service(CHROME_DRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_experimental_option("useAutomationExtension", False)

wd = webdriver.Chrome(service=service, options=options)

# Utils
def download_image(url: str, filename: str, download_path: str = DOWNLOAD_DIR):
    os.makedirs(download_path, exist_ok=True)
    try:
        image_content = requests.get(url, timeout=10).content
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file)
        # Convert mode if needed
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        file_path = os.path.join(download_path, filename)
        image.save(file_path, "JPEG")
        print(f"✅ Success downloaded file {filename}")
    except Exception as e:
        print(f"❌ FAILED: Could not download {filename} - {e}")

def scroll_down(scroll_pause = SCROLL_PAUSE):
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause)

# Main scraping function
def get_images_from_google(query: str, max_scroll: int = 4, max_images: int = 100, max_non_addition: int = 1000):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
    wd.get(url)

    # Đợi ảnh load xong
    WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.YQ4gaf")))
    thumbnails = wd.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")

    print(f"Found {len(thumbnails)} images.")

    skips = 0
    current_scroll = 0
    non_addition_count = 0
    while current_scroll < max_scroll:
        scroll_down()
        current_scroll += 1

        if non_addition_count >= max_non_addition:
            print(f"⚠️ Max Time Out for Non Addition: {non_addition_count}!")
            break

        WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.YQ4gaf")))
        thumbnails = wd.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")
        for idx in range(len(thumbnails)):
            # Get image index and avoid double counting
            c_idx = idx + skips
            try:
                img = thumbnails[c_idx]
            except:
                non_addition_count += 1
                print(f"⚠️ Skip index {c_idx} / {len(thumbnails)}!")
                continue

            try:
                # kiểm tra kích thước
                natural_width = wd.execute_script("return arguments[0].naturalWidth;", img)
                natural_height = wd.execute_script("return arguments[0].naturalHeight;", img)
                # print("Natural size:", natural_width, "x", natural_height)

                if natural_width >= 100 and natural_height >= 100:
                    wd.execute_script("arguments[0].scrollIntoView({block:'center'});", img)
                    img.click()
                    time.sleep(1.5)

                    big_img = wd.find_elements(By.CSS_SELECTOR, "img.sFlh5c.FyHeAf.iPVvYb")
                    try:
                        src = big_img[0].get_attribute("src")
                    except IndexError as e:
                        print(f"Out of Index Error: big_img has {len(big_img)} elements.")
                    IMAGE_URLS.add(src)
                    print(f"✅ Added full-res image ({len(IMAGE_URLS)} images; {current_scroll} scrolls): {src}")
                    
                    # Add skips and Reset non-addition
                    skips += 1
                    non_addition_count = 0
                else:
                    skips += 1
                    non_addition_count += 1
                    print("⚠️ Skipped small thumbnail")
            except Exception as e:
                skips += 1
                non_addition_count += 1
                print("❌ Error loading image -", e)

        if len(IMAGE_URLS) >= max_images:
            break

        print(f"\n🎯 Total collected: {len(IMAGE_URLS)}")
    return IMAGE_URLS

# Use it and download images
if __name__ == "__main__":
    try:
        query = "wooden spoon"
        urls = get_images_from_google(query, max_images=400, max_scroll=10)
    finally:
        # 10m 45.9 for 100 images
        wd.quit()

    print(f"The number of image links: {len(IMAGE_URLS)}.")
    for idx, url in enumerate(IMAGE_URLS):
        download_image(url, f"{idx}.jpg")
        time.sleep(1)