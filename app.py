from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import logging
import os
import random
import time
import json

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_chrome_options(use_proxy=False, headless=True):
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    if use_proxy:
        # Ücretsiz proxy listesi
        proxies = [
            '103.152.112.162:80',
            '193.239.86.249:3128',
            '195.158.3.198:3128'
        ]
        proxy = random.choice(proxies)
        chrome_options.add_argument(f'--proxy-server={proxy}')
    
    return chrome_options

def check_single_url(url, anchor=None, price=None, stock=None, use_proxy=False, headless=True, take_screenshot=False):
    driver = None
    try:
        logger.info(f"URL kontrolü başlıyor: {url}")
        logger.info(f"Proxy: {use_proxy}, Headless: {headless}, Screenshot: {take_screenshot}")
        
        options = get_chrome_options(use_proxy, headless)
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        # URL'yi ziyaret et
        driver.get(url)
        time.sleep(3)  # Sayfanın yüklenmesi için bekle
        
        result = {
            'status': 200,  # Selenium direkt status code vermez
            'url': url,
            'accessible': True,
            'anchor': 0,
            'price': '-',
            'stock': 0
        }
        
        # Ekran görüntüsü al
        if take_screenshot:
            screenshot = driver.get_screenshot_as_png()
            result['screenshot'] = base64.b64encode(screenshot).decode('utf-8')
        
        # Anchor kontrolü
        if anchor:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, anchor))
                )
                result['anchor'] = 1
                result['anchor_text'] = element.text.strip()
            except:
                result['anchor'] = 0
        
        # Fiyat kontrolü
        if price:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, price))
                )
                price_text = element.text.strip()
                result['price'] = extract_price(price_text)
                result['price_raw'] = price_text
            except:
                result['price'] = '-'
        
        # Stok kontrolü
        if stock:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, stock))
                )
                result['stock'] = 1
                result['stock_text'] = element.text.strip()
            except:
                result['stock'] = 0
        
        logger.info(f"Sonuç: {json.dumps(result, ensure_ascii=False)}")
        return result, None
        
    except Exception as e:
        logger.error(f"URL kontrol hatası: {str(e)}")
        return None, str(e)
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def extract_price(text):
    if not text:
        return '-'
    import re
    price_pattern = r'\d+[.,]\d{2}'
    match = re.search(price_pattern, text)
    if match:
        return match.group()
    return '-'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_url', methods=['POST'])
def check_url():
    try:
        data = request.get_json()
        url = data.get('url')
        anchor = data.get('anchor')
        price = data.get('price')
        stock = data.get('stock')
        use_proxy = data.get('useProxy', False)
        headless = data.get('headless', True)
        take_screenshot = data.get('screenshot', False)
        
        if not url:
            return jsonify({'error': 'URL gerekli'}), 400

        result, error = check_single_url(
            url=url,
            anchor=anchor,
            price=price,
            stock=stock,
            use_proxy=use_proxy,
            headless=headless,
            take_screenshot=take_screenshot
        )
        
        if error:
            return jsonify({
                'error': f'Bir hata oluştu: {error}',
                'status': 500,
                'url': url,
                'accessible': False,
                'anchor': 0,
                'price': '-',
                'stock': 0
            }), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        return jsonify({
            'error': f'Bir hata oluştu: {str(e)}',
            'status': 500,
            'url': url,
            'accessible': False,
            'anchor': 0,
            'price': '-',
            'stock': 0
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
