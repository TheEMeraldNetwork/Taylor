// Configurazione
const API_BASE_URL = 'http://localhost:5000/api';  // In produzione cambierà
const STORES_FILTER = ['store.taylorswift.com', 'universalmusic.com', 'amazon.com', 'etsy.com'];

// Gestione Wishlist
let wishlist = JSON.parse(localStorage.getItem('taylorWishlist')) || {};

// Funzioni API
async function searchProducts(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        displayProducts(data);
    } catch (error) {
        console.error('Search error:', error);
        displayError('Search failed. Please try again.');
    }
}

// UI Functions
function displayProducts(products) {
    const resultsArea = document.getElementById('resultsArea');
    resultsArea.innerHTML = products.length ? products.map(product => createProductCard(product)).join('') 
                                          : '<p class="text-center text-gray-500">No products found</p>';
    updateWishlistButtons();
}

function createProductCard(product) {
    return `
        <div class="product-card bg-white rounded-xl shadow-lg overflow-hidden">
            <div class="h-64 overflow-hidden">
                <img src="${product.image || 'images/placeholder.png'}" 
                     alt="${product.title}" 
                     class="w-full h-full object-cover"
                     onerror="this.src='images/placeholder.png'"/>
            </div>
            <div class="p-6">
                <div class="flex justify-between items-start">
                    <h2 class="font-bold text-xl text-purple-900">${product.title}</h2>
                    <button onclick="toggleWishlist('${product.id}', '${product.title}', '${product.price}', '${product.image}')"
                            data-product-id="${product.id}"
                            class="p-2 rounded-full hover:bg-purple-50">
                        <i class="fas fa-heart"></i>
                    </button>
                </div>
                <p class="text-green-600 font-semibold my-2">${product.price}</p>
                <p class="text-gray-600 text-sm mb-4">${product.description}</p>
                <div class="flex justify-between items-center">
                    <span class="text-sm text-purple-600">${product.source}</span>
                    <a href="${product.link}" target="_blank" 
                       class="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700">
                        View Product
                    </a>
                </div>
            </div>
        </div>
    `;
}

// Event Handlers
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    
    // Search on Enter
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchProducts(searchInput.value);
        }
    });

    // Quick search buttons
    document.querySelectorAll('[data-quick-search]').forEach(button => {
        button.addEventListener('click', () => {
            const query = button.dataset.quickSearch;
            searchInput.value = query;
            searchProducts(query);
        });
    });

    // Initialize
    updateWishlistCount();
    // Load initial products
    searchProducts('');
});

// Wishlist Functions
function toggleWishlist(productId, title, price, image) {
    if (wishlist[productId]) {
        delete wishlist[productId];
    } else {
        wishlist[productId] = { title, price, image, notes: '' };
    }
    localStorage.setItem('taylorWishlist', JSON.stringify(wishlist));
    updateWishlistUI();
}

function updateWishlistUI() {
    updateWishlistCount();
    updateWishlistButtons();
    updateWishlistTable();
}

function updateWishlistCount() {
    document.getElementById('wishlistCount').textContent = Object.keys(wishlist).length;
}

function updateWishlistButtons() {
    document.querySelectorAll('[data-product-id]').forEach(button => {
        const productId = button.dataset.productId;
        const icon = button.querySelector('i');
        if (wishlist[productId]) {
            icon.classList.add('text-red-500');
        } else {
            icon.classList.remove('text-red-500');
        }
    });
}
