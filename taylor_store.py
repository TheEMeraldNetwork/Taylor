import requests
import json
import os
from datetime import datetime
import logging
import time
from pathlib import Path
import hashlib
import sys

class TaylorStoreGenerator:
    def __init__(self):
        self.api_key = "AIzaSyCOOon7Dci3yacwBwxm5yHS7P7g0kofzGs"
        self.search_engine_id = "60f3d97ca3e7348dd"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.image_cache_dir = "cache/images"
        self.output_dir = "output"
        self.html_template = self.get_template()
        self.setup()
        self.taylor_domains = [
            "store.taylorswift.com",
            "shop.universalmusic.com",
            "amazon.com/Taylor-Swift",
            "etsy.com/market/taylor_swift"
        ]

    def setup(self):
        for directory in [self.image_cache_dir, self.output_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                          handlers=[logging.StreamHandler(sys.stdout)])

    def search_products(self, query):
        taylor_query = f"Taylor Swift merchandise {query}"
        sites_filter = " OR ".join(f"site:{domain}" for domain in self.taylor_domains)
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': f"{taylor_query} ({sites_filter})",
            'num': 10
        }
        try:
            logging.info(f"Searching for: {taylor_query}")
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code == 429:
                logging.error("API quota exceeded. Waiting before retry...")
                time.sleep(60)
                return self.search_products(query)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Search error: {e}")
            return None

    def download_image(self, url, title="", retries=3):
        if not url or 'http' not in url:
            return 'images/placeholder.png'

        safe_title = "".join(x for x in title if x.isalnum() or x in [' ', '-', '_'])[:50]
        cache_key = hashlib.md5(f"{url}{safe_title}".encode()).hexdigest()[:10]
        cache_path = Path(self.image_cache_dir) / f"{cache_key}.png"

        if cache_path.exists():
            return str(cache_path)

        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                if response.headers.get('content-type', '').startswith('image'):
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, 'wb') as f:
                        f.write(response.content)
                    return str(cache_path)
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Image download failed for {title}: {e}")
                time.sleep(1)
        
        return 'images/placeholder.png'

    def process_products(self, results):
        products = []
        if not results or 'items' not in results:
            return products

        for item in results.get('items', []):
            try:
                title = item.get('title', '').split('-')[0].strip()
                product = {
                    'id': hashlib.md5(title.encode()).hexdigest()[:10],
                    'title': title,
                    'description': item.get('snippet', '').replace('\n', ' '),
                    'link': item.get('link', ''),
                    'price': 'Check price',
                    'image_path': 'images/placeholder.png',
                    'source': next((domain.split('/')[0] for domain in self.taylor_domains 
                                  if domain in item.get('link', '')), 'Other')
                }

                if 'pagemap' in item:
                    if 'cse_image' in item['pagemap']:
                        img_url = item['pagemap']['cse_image'][0].get('src')
                        if img_url:
                            product['image_path'] = self.download_image(img_url, title)
                    
                    if 'product' in item['pagemap']:
                        price = item['pagemap']['product'][0].get('price')
                        if price:
                            product['price'] = f"${price}"

                products.append(product)
                logging.info(f"Processed product: {product['title']}")
            except Exception as e:
                logging.error(f"Error processing product: {e}")
                continue

        return products

    def generate_product_cards(self, products):
        cards = []
        for product in products:
            safe_title = product['title'].replace("'", "\\'").replace('"', '\\"')
            card = f"""
                <div class="product-card bg-white rounded-xl shadow-lg overflow-hidden">
                    <div class="h-64 overflow-hidden">
                        <img src="../{product['image_path']}" 
                             alt="{safe_title}" 
                             class="w-full h-full object-cover"
                             onerror="this.src='images/placeholder.png'"/>
                    </div>
                    <div class="p-6">
                        <div class="flex justify-between items-start">
                            <h2 class="font-bold text-xl text-purple-900">{safe_title}</h2>
                            <button onclick="toggleWishlist('{product['id']}', '{safe_title}', '{product['price']}', '../{product['image_path']}')"
                                    data-product-id="{product['id']}"
                                    class="p-2 rounded-full hover:bg-purple-50">
                                <i class="fas fa-heart"></i>
                            </button>
                        </div>
                        <p class="text-green-600 font-semibold my-2">{product['price']}</p>
                        <p class="text-gray-600 text-sm mb-4">{product['description']}</p>
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-purple-600">{product['source']}</span>
                            <a href="{product['link']}" target="_blank" 
                               class="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700">
                                View Product
                            </a>
                        </div>
                    </div>
                </div>
            """
            cards.append(card)
        return '\n'.join(cards)

    def generate_html(self, products):
        html_content = self.html_template.replace('{date}', datetime.now().strftime("%d/%m/%Y %H:%M"))
        html_content = html_content.replace('{products}', self.generate_product_cards(products))
        
        output_file = Path('index.html')
        output_file.write_text(html_content, encoding='utf-8')
        
        return str(output_file)

    def run(self):
        logging.info("Starting search...")
        products = []
        
        search_queries = [
            "eras tour merch",
            "official store products",
            "collectibles authentic",
            "new arrivals"
        ]

        for query in search_queries:
            results = self.search_products(query)
            if results:
                new_products = self.process_products(results)
                products.extend(new_products)
                logging.info(f"Found {len(new_products)} products for query: {query}")
            time.sleep(2)

        unique_products = {p['title']: p for p in products}.values()
        
        if unique_products:
            output_file = self.generate_html(unique_products)
            logging.info(f"Store generated successfully: {output_file}")
            return output_file
        else:
            logging.error("No products found!")
            return None

if __name__ == "__main__":
    try:
        if not os.path.exists('images/placeholder.png'):
            os.makedirs('images', exist_ok=True)
            url = "https://via.placeholder.com/400x400.png?text=Product+Image+Not+Available"
            response = requests.get(url)
            with open('images/placeholder.png', 'wb') as f:
                f.write(response.content)
        
        store = TaylorStoreGenerator()
        output_file = store.run()
        
        if output_file:
            print(f"\nStore generated successfully!")
            print(f"Open this file in your browser: {output_file}")
        else:
            print("\nError: Failed to generate store. Check the logs for details.")
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
