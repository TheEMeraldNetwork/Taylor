### SEZ_ID_001: Imports e setup iniziale
import requests
import json
import os
from datetime import datetime
import logging
import time
from pathlib import Path
import hashlib
import sys

# SEZ_ID_002: Classe principale con inizializzazione
class TaylorStoreGenerator:
    def __init__(self):
        # Configurazione API e paths
        self.api_key = "AIzaSyCOOon7Dci3yacwBwxm5yHS7P7g0kofzGs"
        self.search_engine_id = "60f3d97ca3e7348dd"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.image_cache_dir = "cache/images"
        self.output_dir = "output"
        
        # Stores autorizzati
        self.authorized_stores = [
            "store.taylorswift.com",
            "shop.universalmusic.com",
            "amazon.com/Taylor-Swift",
            "etsy.com/market/taylor_swift"
        ]
        
        # Setup iniziale
        self.setup_environment()

    def setup_environment(self):
        """Inizializzazione ambiente e logging"""
        # Creazione directories
        for directory in [self.image_cache_dir, self.output_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    # SEZ_ID_003: Gestione ricerca e filtraggio
    def search_products(self, query):
        """Ricerca prodotti con filtro per store autorizzati"""
        base_query = "Taylor Swift merchandise"
        stores_filter = " OR ".join(f"site:{store}" for store in self.authorized_stores)
        
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': f"{base_query} {query} ({stores_filter})",
            'num': 10
        }

        try:
            logging.info(f"Searching: {query}")
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 429:
                logging.warning("Rate limit reached. Waiting...")
                time.sleep(60)
                return self.search_products(query)
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Search error: {e}")
            return None

    # SEZ_ID_004: Gestione immagini e cache
    def handle_image(self, url, title="", retries=3):
        """Gestione download e caching immagini con fallback"""
        if not url or 'http' not in url:
            return 'images/placeholder.png'

        # Generazione nome file cache
        safe_title = "".join(c for c in title if c.isalnum() or c in [' ', '-', '_'])[:50]
        cache_key = hashlib.md5(f"{url}{safe_title}".encode()).hexdigest()[:10]
        cache_path = Path(self.image_cache_dir) / f"{cache_key}.png"

        # Check cache
        if cache_path.exists():
            return str(cache_path)

        # Download con retry
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

    # SEZ_ID_005: Processamento prodotti
    def process_products(self, results):
        """Elaborazione risultati ricerca in prodotti strutturati"""
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
                    'source': next((domain.split('/')[0] for domain in self.authorized_stores 
                                  if domain in item.get('link', '')), 'Other Store')
                }

                # Estrazione metadati
                if 'pagemap' in item:
                    if 'cse_image' in item['pagemap']:
                        img_url = item['pagemap']['cse_image'][0].get('src')
                        if img_url:
                            product['image_path'] = self.handle_image(img_url, title)
                    
                    if 'product' in item['pagemap']:
                        price = item['pagemap']['product'][0].get('price')
                        if price:
                            product['price'] = f"${price}"

                products.append(product)
                logging.info(f"Processed: {product['title']}")
            except Exception as e:
                logging.error(f"Product processing error: {e}")
                continue

        return products

    # SEZ_ID_006: Template HTML e componenti UI
    def get_html_template(self):
        """Template HTML base con stili e script integrati"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taylor Swift Store Helper</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gradient-to-r from-purple-50 to-pink-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-purple-800 mb-2">Taylor Swift Store Helper</h1>
            <p class="text-gray-600">Da Vittoria per la Family in USA</p>
            <p class="text-sm text-gray-500">Updated: {date}</p>
        </header>

        <!-- Search -->
        <div class="max-w-4xl mx-auto mb-8">
            <div class="bg-white rounded-lg shadow-lg p-6">
                <div class="flex gap-2">
                    <input type="text" id="searchInput" 
                           class="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                           placeholder="Search Taylor Swift merchandise...">
                    <button onclick="performSearch()" 
                            class="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700">
                        Search
                    </button>
                </div>
                <div class="mt-4 flex flex-wrap gap-2">
                    <button onclick="quickSearch('eras tour')" 
                            class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200">
                        Eras Tour
                    </button>
                    <button onclick="quickSearch('merchandise')" 
                            class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200">
                        Merchandise
                    </button>
                    <button onclick="quickSearch('clothing')" 
                            class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200">
                        Clothing
                    </button>
                </div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="mb-8">
            <div class="flex justify-between items-center">
                <div class="flex space-x-4">
                    <button onclick="showTab('results')" 
                            class="px-4 py-2 bg-purple-600 text-white rounded-lg">
                        Results
                    </button>
                    <button onclick="showTab('wishlist')" 
                            class="px-4 py-2 bg-white text-purple-600 rounded-lg">
                        Wishlist (<span id="wishlistCount">0</span>)
                    </button>
                </div>
            </div>
        </div>

        <!-- Results Area -->
        <div id="resultsArea" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products}
        </div>

        <!-- Wishlist Area -->
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
// Gestione Wishlist
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

function performSearch() {
    const query = document.getElementById('searchInput').value;
    // Qui andrebbe l'integrazione con l'API di ricerca
    filterResults(query);
}

function quickSearch(term) {
    document.getElementById('searchInput').value = term;
    performSearch();
}

function filterResults(query) {
    query = query.toLowerCase();
    const cards = document.querySelectorAll('.product-card');
    let visibleCount = 0;
    
    cards.forEach(card => {
        const content = card.textContent.toLowerCase();
        if (content.includes(query)) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    updateWishlistCount();
    Object.keys(wishlist).forEach(updateWishlistButtons);
    
    // Enter key trigger search
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});
</script>
</body>
</html>
"""

    # SEZ_ID_007: Generazione output
    def generate_product_cards(self, products):
        """Generazione cards HTML per i prodotti"""
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
#codice collegato manualmente#
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
        """Generazione file HTML finale"""
        html_content = self.get_html_template().replace('{date}', datetime.now().strftime("%d/%m/%Y %H:%M"))
        html_content = html_content.replace('{products}', self.generate_product_cards(products))
        
        output_file = Path('index.html')
        output_file.write_text(html_content, encoding='utf-8')
        
        return str(output_file)

    # SEZ_ID_008: Main e gestione errori
    def run(self):
        """Metodo principale di esecuzione"""
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
