from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
import base64

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def check_single_url(url, anchor=None, price=None, stock=None, use_proxy=False, headless=True, take_screenshot=False):
    driver = None
    try:
        driver = get_driver(headless)
        driver.get(url)
        
        result = {
            'status': 200,  # Selenium direkt status code vermez
            'url': url,
            'accessible': True
        }
        
        # Selektörleri kontrol et
        if anchor:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, anchor))
                )
                result['anchor_text'] = element.text
            except:
                result['anchor_text'] = 'Bulunamadı'
        
        if price:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, price))
                )
                result['price_text'] = element.text
            except:
                result['price_text'] = 'Bulunamadı'
        
        if stock:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, stock))
                )
                result['stock_text'] = element.text
            except:
                result['stock_text'] = 'Bulunamadı'
        
        # Ekran görüntüsü al
        if take_screenshot:
            screenshot = driver.get_screenshot_as_png()
            result['screenshot'] = base64.b64encode(screenshot).decode()
        
        return result, None
        
    except Exception as e:
        logger.error(f"Selenium hatası: {str(e)}")
        return None, str(e)
    
    finally:
        if driver:
            driver.quit()

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
            url, 
            anchor, 
            price, 
            stock, 
            use_proxy, 
            headless, 
            take_screenshot
        )
        
        if error:
            return jsonify({'error': f'Bir hata oluştu: {error}'}), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
