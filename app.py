from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import logging
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_single_url(url, anchor=None, price=None, stock=None, headless=True):
    try:
        with sync_playwright() as p:
            # Browser launch ayarlarını güncelle
            browser_type = p.chromium
            browser = browser_type.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--no-sandbox',
                ],
                chromium_sandbox=False,
                executable_path=os.environ.get('PLAYWRIGHT_BROWSERS_PATH', None)
            )
            
            context = browser.new_context()
            page = context.new_page()
            
            try:
                response = page.goto(url, wait_until="networkidle", timeout=30000)
                status = response.status if response else None
                
                result = {
                    'status': status,
                    'url': url,
                    'accessible': status == 200
                }
                
                if status == 200:
                    if anchor:
                        try:
                            result['anchor_text'] = page.locator(anchor).first().inner_text()
                        except:
                            result['anchor_text'] = 'Bulunamadı'
                            
                    if price:
                        try:
                            result['price_text'] = page.locator(price).first().inner_text()
                        except:
                            result['price_text'] = 'Bulunamadı'
                            
                    if stock:
                        try:
                            result['stock_text'] = page.locator(stock).first().inner_text()
                        except:
                            result['stock_text'] = 'Bulunamadı'
                
                return result, None
                
            except Exception as e:
                logger.error(f"URL kontrol hatası: {str(e)}")
                return None, str(e)
            
            finally:
                try:
                    context.close()
                    browser.close()
                except:
                    pass
                
    except Exception as e:
        logger.error(f"Playwright hatası: {str(e)}")
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
            return jsonify({'error': f'Bir hata oluştu: {error}'}), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
