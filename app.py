from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from requests_html import HTMLSession
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

def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/122.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Firefox/123.0'
    ]
    return random.choice(user_agents)

def check_single_url(url, anchor=None, price=None, stock=None, use_proxy=False, headless=True, take_screenshot=False):
    try:
        logger.info(f"URL kontrolü başlıyor: {url}")
        
        session = HTMLSession()
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        proxies = None
        if use_proxy:
            proxy_list = [
                'http://103.152.112.162:80',
                'http://193.239.86.249:3128',
                'http://195.158.3.198:3128'
            ]
            proxy = random.choice(proxy_list)
            proxies = {
                'http': proxy,
                'https': proxy
            }
        
        response = session.get(
            url, 
            headers=headers, 
            proxies=proxies if use_proxy else None
        )
        
        # JavaScript'i çalıştır
        response.html.render(timeout=20)
        
        result = {
            'status': response.status_code,
            'url': url,
            'accessible': response.status_code == 200,
            'anchor': 0,
            'price': '-',
            'stock': 0
        }
        
        if response.status_code == 200:
            # Ekran görüntüsü
            if take_screenshot:
                try:
                    screenshot = response.html.screenshot(full=True)
                    result['screenshot'] = base64.b64encode(screenshot).decode('utf-8')
                except:
                    logger.warning("Ekran görüntüsü alınamadı")
            
            # Anchor kontrolü
            if anchor:
                elements = response.html.find(anchor)
                if elements:
                    result['anchor'] = 1
                    result['anchor_text'] = elements[0].text
            
            # Fiyat kontrolü
            if price:
                elements = response.html.find(price)
                if elements:
                    price_text = elements[0].text
                    result['price'] = extract_price(price_text)
                    result['price_raw'] = price_text
            
            # Stok kontrolü
            if stock:
                elements = response.html.find(stock)
                result['stock'] = 1 if elements else 0
                if elements:
                    result['stock_text'] = elements[0].text
        
        return result, None
        
    except Exception as e:
        logger.error(f"URL kontrol hatası: {str(e)}")
        return None, str(e)

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
