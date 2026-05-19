// EcoByLive Cart System
let cart = JSON.parse(localStorage.getItem('ecobylive_cart') || '[]');

function saveCart() {
    localStorage.setItem('ecobylive_cart', JSON.stringify(cart));
    updateCartUI();
}

function addToCart(id, name, price) {
    const existing = cart.find(i => i.id === id);
    if (existing) {
        existing.qty += 1;
    } else {
        cart.push({ id, name, price, qty: 1 });
    }
    saveCart();
    // Flash the cart button
    const btn = document.getElementById('cartCount');
    btn.style.transform = 'scale(1.4)';
    setTimeout(() => btn.style.transform = 'scale(1)', 200);
}

function removeFromCart(id) {
    cart = cart.filter(i => i.id !== id);
    saveCart();
}

function updateCartUI() {
    const total = cart.reduce((sum, i) => sum + i.qty, 0);
    const totalPrice = cart.reduce((sum, i) => sum + i.price * i.qty, 0);

    document.getElementById('cartCount').textContent = total;
    document.getElementById('cartTotal').textContent = totalPrice.toFixed(2) + ' kr';

    const itemsEl = document.getElementById('cartItems');
    if (cart.length === 0) {
        itemsEl.innerHTML = '<div class="cart-empty">Din varukorg är tom 🌿</div>';
        return;
    }
    itemsEl.innerHTML = cart.map(item => `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">${item.qty} × ${item.price.toFixed(2)} kr</div>
            </div>
            <button class="cart-item-remove" onclick="removeFromCart(${item.id})">✕</button>
        </div>
    `).join('');
}

function toggleCart() {
    const drawer = document.getElementById('cartDrawer');
    const overlay = document.getElementById('cartOverlay');
    drawer.classList.toggle('open');
    overlay.classList.toggle('open');
}

function openCheckout() {
    if (cart.length === 0) return;
    document.getElementById('checkoutModal').style.display = 'flex';
}

function closeCheckout() {
    document.getElementById('checkoutModal').style.display = 'none';
}

async function placeOrder() {
    const name = document.getElementById('checkoutName').value.trim();
    const email = document.getElementById('checkoutEmail').value.trim();
    if (!name || !email) {
        alert('Fyll i ditt namn och e-post.');
        return;
    }
    try {
        const res = await fetch('/api/cart/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, items: cart })
        });
        const data = await res.json();
        if (data.success) {
            cart = [];
            saveCart();
            closeCheckout();
            toggleCart();
            alert('✅ Tack för din beställning, ' + name + '! Vi hör av oss.');
        }
    } catch (e) {
        alert('Något gick fel. Försök igen.');
    }
}

function toggleNav() {
    const links = document.querySelector('.nav-links');
    if (links) links.classList.toggle('mobile-open');
}

// Init
updateCartUI();
