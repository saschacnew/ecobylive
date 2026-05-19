from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'ecobylife-secret-2024'

UPLOAD_FOLDER = 'static/images/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CONTACT_EMAIL = 'your@email.com'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = sqlite3.connect('ecobylife.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            image TEXT,
            featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            product_id INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    try:
        db.execute("INSERT INTO admins (username, password) VALUES (?, ?)",
                   ('admin', generate_password_hash('admin123')))
    except:
        pass
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        products = [
            ('Rosehip Face Serum', 'Rich in vitamin C and antioxidants. Brightens and evens skin tone naturally.', 'Skincare', None, 1),
            ('Green Clay Mask', 'Deep cleansing clay mask with eucalyptus and green tea extracts.', 'Skincare', None, 1),
            ('Hemp Lip Balm', 'Nourishing lip balm with hemp seed oil and shea butter.', 'Skincare', None, 0),
            ('Vegan Mascara', 'Lengthening mascara formula. 100% vegan and cruelty-free.', 'Makeup', None, 1),
            ('Natural Foundation', 'Lightweight coverage with SPF 20. Available in 12 shades.', 'Makeup', None, 0),
            ('Berry Lip Tint', 'Sheer tinted lip balm with wild berry pigments.', 'Makeup', None, 1),
            ('Argan Hair Oil', 'Frizz-taming serum with pure Moroccan argan oil.', 'Haircare', None, 1),
            ('Bamboo Shampoo', 'Strengthening shampoo with bamboo extract and biotin.', 'Haircare', None, 0),
            ('Cedar & Moss EDP', 'Earthy unisex fragrance with cedar, vetiver and green moss.', 'Fragrance', None, 1),
            ('Wildflower Mist', 'Light botanical body mist with Swedish wildflower extracts.', 'Fragrance', None, 0),
        ]
        for p in products:
            db.execute("INSERT INTO products (name, description, category, image, featured) VALUES (?,?,?,?,?)", p)
    db.commit()
    db.close()

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
init_db()

@app.route('/')
def index():
    db = get_db()
    featured = db.execute("SELECT * FROM products WHERE featured=1 LIMIT 6").fetchall()
    db.close()
    return render_template('index.html', featured=featured)

@app.route('/catalog')
def catalog():
    category = request.args.get('category', 'All')
    db = get_db()
    if category == 'All':
        products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    else:
        products = db.execute("SELECT * FROM products WHERE category=? ORDER BY created_at DESC", (category,)).fetchall()
    db.close()
    return render_template('catalog.html', products=products, active_category=category)

@app.route('/product/<int:product_id>')
def product(product_id):
    db = get_db()
    p = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    related = db.execute("SELECT * FROM products WHERE category=? AND id!=? LIMIT 4", (p['category'], product_id)).fetchall()
    db.close()
    return render_template('product.html', product=p, related=related)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        product_id = request.form.get('product_id')
        db = get_db()
        db.execute("INSERT INTO enquiries (name, email, product_id, message) VALUES (?,?,?,?)",
                   (name, email, product_id or None, message))
        db.commit()
        db.close()
        flash('Tack! Vi återkommer inom kort.')
        return redirect(url_for('contact'))
    db = get_db()
    products = db.execute("SELECT id, name FROM products ORDER BY name").fetchall()
    db.close()
    preselect = request.args.get('product')
    return render_template('contact.html', products=products, preselect=preselect)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        db = get_db()
        admin = db.execute("SELECT * FROM admins WHERE username=?", (request.form['username'],)).fetchone()
        db.close()
        if admin and check_password_hash(admin['password'], request.form['password']):
            session['admin'] = admin['username']
            return redirect(url_for('admin_dashboard'))
        flash('Fel användarnamn eller lösenord.')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    enquiries = db.execute("""
        SELECT e.*, p.name as product_name 
        FROM enquiries e 
        LEFT JOIN products p ON e.product_id = p.id 
        ORDER BY e.created_at DESC LIMIT 50
    """).fetchall()
    stats = {
        'total_products': db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'total_enquiries': db.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0],
    }
    db.close()
    return render_template('admin_dashboard.html', products=products, enquiries=enquiries, stats=stats)

@app.route('/admin/product/new', methods=['GET', 'POST'])
@admin_required
def admin_new_product():
    if request.method == 'POST':
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        db = get_db()
        db.execute("INSERT INTO products (name, description, category, image, featured) VALUES (?,?,?,?,?)",
                   (request.form['name'], request.form['description'],
                    request.form['category'], image_filename,
                    1 if request.form.get('featured') else 0))
        db.commit()
        db.close()
        flash('Produkt tillagd!')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_product_form.html', product=None)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    db = get_db()
    p = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if request.method == 'POST':
        image_filename = p['image']
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        db.execute("UPDATE products SET name=?, description=?, category=?, image=?, featured=? WHERE id=?",
                   (request.form['name'], request.form['description'],
                    request.form['category'], image_filename,
                    1 if request.form.get('featured') else 0, product_id))
        db.commit()
        flash('Produkt uppdaterad!')
        return redirect(url_for('admin_dashboard'))
    db.close()
    return render_template('admin_product_form.html', product=p)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (product_id,))
    db.commit()
    db.close()
    flash('Produkt raderad.')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
