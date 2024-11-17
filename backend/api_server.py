# SEZ_ID_001: Backend (api_server.py)
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import logging
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

class TaylorSwiftAPI:
    def __init__(self):
        self.api_key = "AIzaSyCOOon7Dci3yacwBwxm5yHS7P7g0kofzGs"
        self.search_engine_id = "60f3d97ca3e7348dd"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.authorized_stores = [
            "store.taylorswift.com",
            "shop.universalmusic.com",
            "amazon.com/Taylor-Swift",
            "etsy.com/market/taylor_swift"
        ]

    def search_products(self, query):
        taylor_query = f"Taylor Swift merchandise {query}"
        sites_filter = " OR ".join(f"site:{domain}" for domain in self.authorized_stores)
        
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': f"{taylor_query} ({sites_filter})",
            'num': 10
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return self.process_results(response.json())
        except Exception as e:
            logging.error(f"Search error: {e}")
            return []

    def process_results(self, results):
        if not results or 'items' not in results:
            return []

        processed_items = []
        for item in results.get('items', []):
            try:
                product = {
                    'title': item.get('title', '').split('-')[0].strip(),
                    'description': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'price': 'Check price',
                    'image': self.get_image_url(item),
                    'source': next((domain.split('/')[0] for domain in self.authorized_stores 
                                  if domain in item.get('link', '')), 'Other Store')
                }
                processed_items.append(product)
            except Exception as e:
                logging.error(f"Error processing item: {e}")
                continue

        return processed_items

    def get_image_url(self, item):
        try:
            if 'pagemap' in item:
                if 'cse_image' in item['pagemap']:
                    return item['pagemap']['cse_image'][0].get('src', '')
            return ''
        except Exception:
            return ''

api = TaylorSwiftAPI()

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = api.search_products(query)
    return jsonify(results)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "timestamp": str(datetime.now())})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
