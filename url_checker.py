from playwright.sync_api import sync_playwright
import logging
import base64

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class URLChecker:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def check_url(self, url, selectors, use_proxy=False, headless=True):
        logger.info(f"URL kontrolü başlıyor: {url}")
        logger.info(f"Selektörler: {selectors}")
        
        try:
            with sync_playwright() as p:
                # Tarayıcı ayarları
                browser_args = ['--start-maximized']
                if use_proxy:
                    # Proxy ayarlarını ekleyin
                    browser_args.append(f'--proxy-server=your-proxy-here')

                # Tarayıcıyı başlat
                browser = p.chromium.launch(
                    headless=headless,  # headless=False yaparak tarayıcıyı görebilirsiniz
                    args=browser_args
                )

                # Yeni bir sayfa oluştur
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=self.headers['User-Agent']
                )
                page = context.new_page()

                # Sayfayı yükle
                logger.info("Sayfa yükleniyor...")
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Sonuçları sakla
                results = {
                    'anchor': 0,
                    'price': '-',
                    'stock': 0,
                    'screenshot': None
                }

                # Anchor kontrolü
                logger.info("Anchor kontrolü yapılıyor...")
                try:
                    anchor_element = page.locator(selectors['anchor']).first
                    if anchor_element:
                        results['anchor'] = 1
                        logger.info("Anchor bulundu")
                except Exception as e:
                    logger.error(f"Anchor bulunamadı: {e}")

                # Fiyat kontrolü
                logger.info("Fiyat kontrolü yapılıyor...")
                try:
                    price_element = page.locator(selectors['price']).first
                    if price_element:
                        price_text = price_element.text_content()
                        # Fiyat temizleme
                        price_text = ''.join(c for c in price_text if c.isdigit() or c in '.,')
                        price_text = price_text.replace(',', '.')
                        try:
                            float(price_text)  # Sayı kontrolü
                            results['price'] = price_text
                            logger.info(f"Fiyat bulundu: {price_text}")
                        except ValueError:
                            logger.error("Geçerli bir fiyat formatı bulunamadı")
                except Exception as e:
                    logger.error(f"Fiyat bulunamadı: {e}")

                # Stok kontrolü
                logger.info("Stok kontrolü yapılıyor...")
                try:
                    stock_element = page.locator(selectors['stock']).first
                    if stock_element:
                        results['stock'] = 1
                        logger.info("Stok bulundu")
                except Exception as e:
                    logger.error(f"Stok bulunamadı: {e}")

                # Screenshot al
                logger.info("Ekran görüntüsü alınıyor...")
                try:
                    screenshot_bytes = page.screenshot(full_page=True)
                    results['screenshot'] = base64.b64encode(screenshot_bytes).decode('utf-8')
                    logger.info("Ekran görüntüsü alındı")
                except Exception as e:
                    logger.error(f"Ekran görüntüsü alınamadı: {e}")

                # Tarayıcıyı kapat
                browser.close()
                logger.info("İşlem tamamlandı")
                
                return results

        except Exception as e:
            logger.error(f"Genel hata oluştu: {str(e)}")
            return {
                'anchor': 0,
                'price': '-',
                'stock': 0,
                'screenshot': None,
                'error': str(e)
            }

# Test için
if __name__ == "__main__":
    checker = URLChecker()
    test_data = {
        'url': 'https://janeiredale.se/smooth-affair-mattifying-face-primer',
        'selectors': {
            'anchor': 'h1.x-name',
            'price': '.x-price .g-price',
            'stock': '.x-add-to-cart-buttons'
        }
    }
    
    result = checker.check_url(
        test_data['url'], 
        test_data['selectors'],
        headless=False  # Tarayıcıyı görmek için False yapın
    )
    print("Sonuç:", result)