from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import logging
import os

app = Flask(__name__)

# CORS ayarlarını güncelle - tüm kaynaklara izin ver
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_single_url(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--no-sandbox',
                ]
            )
            
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Timeout süresini artır
                page.set_default_timeout(60000)  # 60 saniye
                response = page.goto(url, wait_until="networkidle")
                status = response.status if response else None
                
                result = {
                    'status': status,
                    'url': url,
                    'accessible': status == 200
                }
                
                return result, None
                
            except Exception as e:
                logger.error(f"URL kontrol hatası: {str(e)}")
                return None, str(e)
            
            finally:
                context.close()
                browser.close()
                
    except Exception as e:
        logger.error(f"Playwright hatası: {str(e)}")
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_url', methods=['POST', 'OPTIONS'])
def check_url():
    # OPTIONS isteği için CORS yanıtı
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL gerekli'}), 400

        result, error = check_single_url(url)
        
        if error:
            return jsonify({'error': f'Bir hata oluştu: {error}'}), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
