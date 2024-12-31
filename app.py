from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # CORS desteği için
from url_checker import URLChecker
import logging

# Logging ayarları
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # CORS desteği ekle
checker = URLChecker()

@app.route('/')
def home():
    logger.info('Ana sayfa istendi')
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    try:
        logger.info('Check endpoint çağrıldı')
        data = request.json
        logger.info(f"Gelen veri: {data}")
        
        url = data.get('url')
        selectors = {
            'anchor': data.get('anchor_selector'),
            'price': data.get('price_selector'),
            'stock': data.get('stock_selector')
        }
        use_proxy = data.get('use_proxy', False)
        headless = data.get('headless', True)
        
        result = checker.check_url(url, selectors, use_proxy=use_proxy, headless=headless)
        logger.info(f"İşlem sonucu: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Hata oluştu: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
