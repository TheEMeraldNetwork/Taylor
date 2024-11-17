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

    def setup(self):
        """Setup directories and logging"""
        for directory in [self.image_cache_dir, self.output_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    def search_products(self, query):
        """Search products using Google Custom Search"""
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': f"{query} (site:amazon.com OR site:etsy.com OR site:store.taylorswift.com)",
            'num': 10
        }
        try:
            logging.info(f"Searching for: {query}")
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

    def download_image(self, url, retries=3):
        """Download and cache images with retry logic"""
        if not url or 'http' not in url:
            return 'placeholder.jpg'

        cache_key = hashlib.md5(url.encode()).hexdigest()[:10]
        cache_path = Path(self.image_cache_dir) / f"{cache_key}.jpg"

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
                else:
                    return 'placeholder.jpg'
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Image download failed: {e}")
                    return 'placeholder.jpg'
                time.sleep(1)

    def process_products(self, results):
        """Process search results into product data"""
        products = []
        if not results or 'items' not in results:
            return products

        for item in results.get('items', []):
            try:
                product = {
                    'title': item.get('title', '').split('-')[0].strip(),
                    'description': item.get('snippet', '').replace('\n', ' '),
                    'link': item.get('link', ''),
                    'price': 'Check price',
                    'image_path': 'placeholder.jpg',
                    'source': 'Taylor Swift Store'
                }

                if 'amazon.com' in product['link']:
                    product['source'] = 'Amazon'
                elif 'etsy.com' in product['link']:
                    product['source'] = 'Etsy'

                if 'pagemap' in item:
                    if 'cse_image' in item['pagemap']:
                        img_url = item['pagemap']['cse_image'][0].get('src')
                        if img_url:
                            product['image_path'] = self.download_image(img_url)
                    
                    if 'product' in item['pagemap']:
                        price = item['pagemap']['product'][0].get('price')
                        if price:
                            product['price'] = f"${price}"
                    
                    if 'metatags' in item['pagemap']:
                        for metatag in item['pagemap']['metatags']:
                            if 'og:image' in metatag:
                                product['image_path'] = self.download_image(metatag['og:image'])
                                break

                products.append(product)
                logging.info(f"Processed product: {product['title']}")
            except Exception as e:
                logging.error(f"Error processing product: {e}")
                continue

        return products

    def get_template(self):
        """Returns the HTML template with embedded Google Custom Search"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taylor Swift Store Helper</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script async src="https://cse.google.com/cse.js?cx=60f3d97ca3e7348dd"></script>
    <style>
        .gsc-control-cse {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
        }
        .gsc-input-box {
            border-radius: 0.5rem !important;
        }
        .gsc-search-button-v2 {
            border-radius: 0.5rem !important;
            padding: 8px 16px !important;
        }
    </style>
</head>
<body class="bg-gradient-to-r from-purple-50 to-pink-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-purple-800 mb-2">Taylor Swift Store Helper</h1>
            <p class="text-gray-600">For Family in USA 🇺🇸</p>
            <p class="text-sm text-gray-500">Updated: {date}</p>
        </header>

        <div class="max-w-4xl mx-auto mb-8">
            <div class="bg-white rounded-lg shadow-lg p-6">
                <div class="gcse-search"></div>
            </div>
        </div>

        <div class="flex justify-between items-center mb-8">
            <div class="flex space-x-4">
                <button onclick="showTab('results')" 
                        class="px-4 py-2 bg-purple-600 text-white rounded-lg">
                    Curated Products
                </button>
                <button onclick="showTab('wishlist')" 
                        class="px-4 py-2 bg-white text-purple-600 rounded-lg">
                    Wishlist (<span id="wishlistCount">0</span>)
                </button>
            </div>
        </div>

        <div id="resultsArea" class="mb-8">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {products}
            </div>
        </div>

        <div id="wishlistArea" class="hidden">
            <div class="bg-white rounded-lg shadow-lg overflow-hidden">
                <table class="min-w-full">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="wishlistBody"></tbody>
                </table>
            </div>
        </div>
    </div>

<script>
let wishlist = JSON.parse(localStorage.getItem('taylorWishlist')) || {};

function showTab(tabName) {
    const resultsArea = document.getElementById('resultsArea');
    const wishlistArea = document.getElementById('wishlistArea');
    
    if (tabName === 'results') {
        resultsArea.classList.remove('hidden');
        wishlistArea.classList.add('hidden');
    } else {
        wishlistArea.classList.remove('hidden');
        resultsArea.classList.add('hidden');
        updateWishlistTable();
    }
}

function toggleWishlist(productId, title, price, image) {
    if (wishlist[productId]) {
        delete wishlist[productId];
    } else {
        wishlist[productId] = {
            title: title,
            price: price,
            image: image,
            notes: ''
        };
    }
    
    localStorage.setItem('taylorWishlist', JSON.stringify(wishlist));
    updateWishlistCount();
    updateWishlistButtons(productId);
    updateWishlistTable();
}

function updateWishlistCount() {
    document.getElementById('wishlistCount').textContent = Object.keys(wishlist).length;
}

function updateWishlistButtons(productId) {
    const buttons = document.querySelectorAll(`[data-product-id="${productId}"]`);
    buttons.forEach(button => {
        const icon = button.querySelector('i');
        if (wishlist[productId]) {
            icon.classList.add('text-red-500');
        } else {
            icon.classList.remove('text-red-500');
        }
    });
}

function updateWishlistTable() {
    const tbody = document.getElementById('wishlistBody');
    tbody.innerHTML = '';
    
    Object.entries(wishlist).forEach(([id, item]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4">
                <div class="flex items-center">
                    <img class="h-10 w-10 rounded-full" src="${item.image}" alt="${item.title}">
                    <div class="ml-4">${item.title}</div>
                </div>
            </td>
            <td class="px-6 py-4">${item.price}</td>
            <td class="px-6 py-4">
                <textarea
                    onchange="updateNotes('${id}', this.value)"
                    class="w-full px-2 py-1 border rounded"
                    placeholder="Add notes..."
                >${item.notes}</textarea>
            </td>
            <td class="px-6 py-4">
                <button onclick="toggleWishlist('${id}')" 
                        class="text-red-600 hover:text-red-900">
                    Remove
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updateNotes(productId, notes) {
    if (wishlist[productId]) {
        wishlist[productId].notes = notes;
        localStorage.setItem('taylorWishlist', JSON.stringify(wishlist));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateWishlistCount();
    Object.keys(wishlist).forEach(updateWishlistButtons);
});
</script>
</body>
</html>'''

    def generate_product_cards(self, products):
        """Generate HTML for product cards"""
        cards = []
        for product in products:
            safe_title = product['title'].replace("'", "\\'").replace('"', '\\"')
            card = f"""
                <div class="product-card bg-white rounded-xl shadow-lg overflow-hidden">
                    <img src="../{product['image_path']}" alt="{safe_title}" class="w-full h-64 object-cover"/>
                    <div class="p-6">
                        <div class="flex justify-between items-start">
                            <h2 class="font-bold text-xl text-purple-900">{safe_title}</h2>
                            <button onclick="toggleWishlist('{hash(safe_title)}', '{safe_title}', '{product['price']}', '../{product['image_path']}')"
                                    data-product-id="{hash(safe_title)}"
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
        """Generate final HTML file"""
        html_content = self.html_template.replace('{date}', datetime.now().strftime("%d/%m/%Y %H:%M"))
        html_content = html_content.replace('{products}', self.generate_product_cards(products))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(self.output_dir) / f'taylor_store_{timestamp}.html'
        output_file.write_text(html_content, encoding='utf-8')
        
        return str(output_file)

    def run(self):
        """Main execution method"""
        logging.info("Starting search...")
        products = []
        
        search_queries = [
            "Taylor Swift merchandise official",
            "Taylor Swift eras tour merch",
            "Taylor Swift official store products",
            "Taylor Swift collectibles authentic"
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
        # Create placeholder image if it doesn't exist
        if not os.path.exists('placeholder.jpg'):
            url = "https://via.placeholder.com/400x400.jpg?text=Product+Image+Not+Available"
            response = requests.get(url)
            with open('placeholder.jpg', 'wb') as f:
                f.write(response.content)
        
        store = TaylorStoreGenerator()
        output_file = store.run()
        
        if output_file:
            print(f"\nStore generated successfully!")
            print(f"Open this file in your browser: {output_file}")
            print("\nNote: Make sure to keep the cache folder alongside the HTML file for images to work.")
        else:
            print("\nError: Failed to generate store. Check the logs for details.")
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
