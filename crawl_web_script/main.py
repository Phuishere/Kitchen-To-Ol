'''
To run this:
python crawl_web_script/main.py
python Kitchen-To-Ol/crawl_web_script/main.py
'''

import os
import time
import io
import argparse
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
BASE = "."
CHROME_DRIVER_PATH = os.path.join(BASE, "resources/chromedriver-win64/chromedriver.exe")

# Search URL
SEARCH_URL = ("https://www.google.com/search?"
            "q={query}&tbm=isch") # basic Google Images query url

# Utils
def download_image(url: str, filename: str, download_dir: str, verbose: bool = True) -> bool:
    os.makedirs(download_dir, exist_ok=True)
    try:
        image_content = requests.get(url, timeout=10).content
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file)
        # Convert mode if needed
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        file_path = os.path.join(download_dir, filename)
        image.save(file_path, "JPEG")
        if verbose:
            print(f"✅ Success downloaded file {filename}")
        return True
    except Exception as e:
        if verbose:
            print(f"❌ FAILED: Could not download {filename} - {e}")
        return False

def scroll_down(wd: webdriver.Chrome, time_pause: float):
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(time_pause)

# Main scraping function
def get_images_from_google(wd: webdriver.Chrome, query: str, max_scroll: int = 4, max_images: int = 100, max_non_addition: int = 1000, time_pause: int = 1, verbose: bool = True):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
    wd.get(url)

    # Đợi ảnh load xong
    WebDriverWait(wd, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.YQ4gaf")))
    thumbnails = wd.find_elements(By.CSS_SELECTOR, "img.YQ4gaf")

    print(f"Found {len(thumbnails)} images.")

    skips = 0
    current_scroll = 0
    non_addition_count = 0
    img_urls = set()
    while current_scroll < max_scroll:
        scroll_down(wd, time_pause)
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

                if natural_width >= 100 and natural_height >= 100:
                    wd.execute_script("arguments[0].scrollIntoView({block:'center'});", img)
                    img.click()
                    time.sleep(time_pause)

                    big_img = wd.find_elements(By.CSS_SELECTOR, "img.sFlh5c.FyHeAf.iPVvYb")
                    try:
                        src = big_img[-1].get_attribute("src")
                    except IndexError as e:
                        if verbose:
                            print(f"Out of Index Error: big_img has {len(big_img)} elements.")
                    img_urls.add(src)
                    print(f"✅ Added full-res image ({len(img_urls)} images; {current_scroll} scrolls): {src}")
                    
                    # Add skips and Reset non-addition
                    skips += 1
                    non_addition_count = 0
                else:
                    skips += 1
                    non_addition_count += 1
                    if verbose:
                        print("⚠️ Skipped small thumbnail")
            except Exception as e:
                skips += 1
                non_addition_count += 1
                if verbose:
                    print("❌ Error loading image -", e)

        if len(img_urls) >= max_images:
            break

        print(f"\n🎯 Total collected (query: '{query}'): {len(img_urls)}")
    return img_urls

def main():
    # Parser
    '''
    Example run:
        python crawl_web_script/main.py "muỗng gỗ" "wooden spoon" "wooden spoons for cooking"
    '''
    parser = argparse.ArgumentParser(
        prog='Kitchen-To-Ol Image Scraping',
        description='A simple program that crawl images.',
        epilog='Thanks for using my program!'
    )
    parser.add_argument(
        '--n_img', type=int,
        metavar='n_img',
        default=1000, # Default
        help='Max number of images for each query (Default: 1000).'
    )
    parser.add_argument(
        '--time_pause', type=float,
        metavar='time_pause',
        default=1.0, # Default
        help='Time pause for queries (Default: 1.0s).'
    )
    parser.add_argument(
        '--max_scroll', type=float,
        metavar='max_scroll',
        default=25, # Default
        help='Max time of scrolling (Default: 25 scrolls).'
    )
    parser.add_argument(
        '--max_error', type=float,
        metavar='max_error',
        default=10000, # Default
        help='Time pause for queries (Default: 1.0s).'
    )
    parser.add_argument(
        '--verbose', type=bool,
        metavar='verbose',
        default=False, # Default
        help='Time pause for queries (Default: 1.0s).'
    )
    parser.add_argument(
        'queries',
        metavar ='Q',
        type = str,
        nargs ='+',
        help ='Image queries that you would like to use!'
    )

    args = parser.parse_args()
    max_non_addition = args.max_error
    time_pause = args.time_pause
    max_images = args.n_img
    verbose = args.verbose
    max_scroll = args.max_scroll
    queries = args.queries
    
    # If no queries input, return
    if not queries:
        return

    # Setup webdriver
    service = Service(CHROME_DRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    wd = webdriver.Chrome(service=service, options=options)

    try:
        for query in queries:
            img_urls = get_images_from_google(wd, query, max_images=max_images, max_scroll=max_scroll, max_non_addition=max_non_addition, time_pause=time_pause, verbose=verbose)

            query = query.replace(" ", "_")
            download_dir = os.path.join(BASE, "resources", query)
            
            # Image link file
            image_link_file = os.path.join(download_dir, "downloaded_images.txt")
            try:
                with open(image_link_file, "x"):
                    print(f"✅ Created link file in: {image_link_file}")
                    existing_urls = []
            except:
                print(f"✅ Downloaded images existing in: {image_link_file}")
                with open(image_link_file, "r") as fr:
                    existing_urls = [url.strip("\n") for url in fr.readlines()]
                    
            # Download
            print(f"The number of image links: {len(img_urls)}.")
            for idx, url in enumerate(img_urls):
                # Get image name
                if 0 <= idx <= 9:
                    idx_str = f"00000{idx}"
                if 10 <= idx <= 99:
                    idx_str = f"0000{idx}"
                if 100 <= idx <= 999:
                    idx_str = f"000{idx}"
                if 1000 <= idx <= 9999:
                    idx_str = f"00{idx}"
                if 10000 <= idx <= 99999:
                    idx_str = f"0{idx}"
                if 100000 <= idx <= 999999:
                    idx_str = f"{idx}"
                
                # Check if url has existed
                if url in existing_urls:
                    continue
                success = download_image(url, f"{query}_{idx_str}.jpg", download_dir=download_dir, verbose=verbose)
                if success:
                    with open(image_link_file, "a") as fa:
                        fa.writelines([url+"\n"])
                time.sleep(time_pause)
    except KeyboardInterrupt:
        print("🎯 Exitting program - - -")
    finally:
        # 10m 45.9 for 100 images
        print("🎯 Program ending! - - -")
        wd.quit()

# Use it and download images
if __name__ == "__main__":
    main()