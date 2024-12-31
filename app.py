from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import logging
import os
import random
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

def check_single_url(url, anchor=None, price=None, stock=None, use_proxy=False):
    try:
        logger.info(f"URL kontrolü başlıyor: {url}")
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'
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
        
        session = requests.Session()
        
        # Ana domain'i ziyaret et
        try:
            domain = url.split('/')[2]
            base_url = f"https://{domain}"
            logger.info(f"Ana domain ziyaret ediliyor: {base_url}")
            session.get(base_url, headers=headers, proxies=proxies, timeout=30)
        except Exception as e:
            logger.warning(f"Ana domain ziyareti başarısız: {str(e)}")
        
        # Hedef URL'yi ziyaret et
        response = session.get(
            url, 
            headers=headers, 
            proxies=proxies,
            timeout=30,
            allow_redirects=True
        )
        
        result = {
            'status': response.status_code,
            'url': url,
            'accessible': response.status_code == 200,
            'anchor': 0,
            'price': '-',
            'stock': 0
        }
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Anchor kontrolü
            if anchor:
                anchor_element = soup.select_one(anchor)
                result['anchor'] = 1 if anchor_element else 0
                if anchor_element:
                    result['anchor_text'] = anchor_element.text.strip()
            
            # Fiyat kontrolü
            if price:
                price_element = soup.select_one(price)
                if price_element:
                    price_text = price_element.text.strip()
                    result['price'] = extract_price(price_text)
                    result['price_raw'] = price_text
            
            # Stok kontrolü
            if stock:
                stock_element = soup.select_one(stock)
                result['stock'] = 1 if stock_element else 0
                if stock_element:
                    result['stock_text'] = stock_element.text.strip()
        
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
        
        if not url:
            return jsonify({'error': 'URL gerekli'}), 400

        result, error = check_single_url(
            url=url,
            anchor=anchor,
            price=price,
            stock=stock,
            use_proxy=use_proxy
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
