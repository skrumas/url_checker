from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import logging
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_price(text):
    if not text:
        return '-'
    # Fiyat formatını kontrol et (123,45 veya 123.45)
    price_pattern = r'\d+[.,]\d{2}'
    match = re.search(price_pattern, text)
    if match:
        return match.group()
    return '-'

def check_single_url(url, anchor=None, price=None, stock=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        result = {
            'status': response.status_code,
            'url': url,
            'accessible': response.status_code == 200,
            'anchor': 0,  # Varsayılan değerler
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
        
        if not url:
            return jsonify({'error': 'URL gerekli'}), 400

        result, error = check_single_url(url, anchor, price, stock)
        
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
