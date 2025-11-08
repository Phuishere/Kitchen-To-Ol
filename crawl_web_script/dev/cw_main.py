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

# ► Configuration
BASE = "E:/projects/_full_fledge/Kitchen-Tools-Project"
DOWNLOAD_DIR = os.path.join(BASE, "resources", "crawled")
CHROME_DRIVER_PATH = "E:/projects/_full_fledge/Kitchen-Tools-Project/resources/chromedriver-win64/chromedriver.exe"

SEARCH_URL = ("https://www.google.com/search?"
              "q={query}&tbm=isch")  # basic Google Images query url

MAX_IMAGES = 400
SCROLL_PAUSE = 1.0   # seconds

# ► Setup webdriver
service = Service(CHROME_DRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_experimental_option("useAutomationExtension", False)

wd = webdriver.Chrome(service=service, options=options)

# ► Utils
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

# ► Main scraping function
def get_images_from_google(query: str, max_scroll: int = 4, max_images: int = 100):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
    wd.get(url)
    image_urls = set()

    # Đợi ảnh load xong
    scroll_down()
    WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.YQ4gaf")))
    thumbnails = wd.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")

    print(f"Found {len(thumbnails)} images.")

    skips = 0
    current_scroll = 0
    while current_scroll < max_scroll:
        scroll_down()
        current_scroll += 1

        WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.YQ4gaf")))
        thumbnails = wd.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")
        for idx in range(len(thumbnails)):
            # Get image index and avoid double counting
            c_idx = idx + len(image_urls) + skips
            try:
                img = thumbnails[c_idx]
            except:
                print(f"⚠️ Skip index {c_idx} / {len(thumbnails)}!")
                continue

            try:
                # kiểm tra kích thước
                natural_width = wd.execute_script("return arguments[0].naturalWidth;", img)
                natural_height = wd.execute_script("return arguments[0].naturalHeight;", img)
                print("Natural size:", natural_width, "x", natural_height)

                if natural_width >= 100 and natural_height >= 100:
                    wd.execute_script("arguments[0].scrollIntoView({block:'center'});", img)
                    img.click()
                    time.sleep(2)

                    big_img = wd.find_elements(By.CSS_SELECTOR, "img.sFlh5c.FyHeAf.iPVvYb")
                    src = big_img[0].get_attribute("src")
                    image_urls.add(src)
                    print(f"✅ Added full-res image: {src}")
                else:
                    skips += 1
                    print("⚠️ Skipped small thumbnail")
            except Exception as e:
                skips += 1
                print("❌ Error loading image -", e)

        if len(image_urls) >= max_images:
            break

        print(f"\n🎯 Total collected: {len(image_urls)}")
    return image_urls

# ► Use it & download images
if __name__ == "__main__":
    try:
        query = "tongs kitchen on table"
        urls = get_images_from_google(query, max_images=MAX_IMAGES)
        for idx, url in enumerate(urls):
            download_image(url, f"{idx}.jpg")
            time.sleep(1)
    finally:
        wd.quit()