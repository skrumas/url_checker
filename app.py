from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import logging

app = Flask(__name__)
CORS(app)

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=True,  # Headless modu açık
        args=[
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-sandbox',
        ]
    )
    return browser, playwright

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_url', methods=['POST'])
def check_url():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL gerekli'}), 400

        browser, playwright = get_browser()
        page = browser.new_page()
        
        try:
            response = page.goto(url)
            status = response.status if response else None
            
            result = {
                'status': status,
                'url': url,
                'accessible': status == 200
            }
            
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"URL kontrol hatası: {str(e)}")
            return jsonify({'error': f'Bir hata oluştu: {str(e)}'}), 500
        
        finally:
            browser.close()
            playwright.stop()
            
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("Flask uygulaması başlatılıyor...")
