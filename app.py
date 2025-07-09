from flask import Flask, request, jsonify, send_from_directory
import os
import json

app = Flask(__name__)

# === Ensure folders exist ===
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

# === File Paths ===
PRODUCTS_FILE = 'data/products.json'
VENDORS_FILE = 'data/vendors.json'
CUSTOMERS_FILE = 'data/customers.json'
DELIVERY_FILE = 'data/delivery.json'

# === PRODUCT ROUTES ===

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.form.to_dict()
    image = request.files.get('image')
    video = request.files.get('video')

    if not image or not video:
        return jsonify({'error': 'Both image and video are required'}), 400

    image_path = os.path.join('uploads', image.filename)
    video_path = os.path.join('uploads', video.filename)
    image.save(image_path)
    video.save(video_path)

    data['image'] = image.filename
    data['video'] = video.filename

    with open(PRODUCTS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

    return jsonify({'message': 'Product saved', 'data': data})

@app.route('/api/products', methods=['GET'])
def get_products():
    products = []
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            for line in f:
                products.append(json.loads(line.strip()))
    return jsonify(products)

# === VENDOR ROUTES ===

@app.route('/api/vendors', methods=['POST'])
def add_vendor():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    with open(VENDORS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

    return jsonify({'message': 'Vendor added', 'data': data})

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    vendors = []
    if os.path.exists(VENDORS_FILE):
        with open(VENDORS_FILE, 'r') as f:
            for line in f:
                vendors.append(json.loads(line.strip()))
    return jsonify(vendors)

# === CUSTOMER ROUTES ===

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    with open(CUSTOMERS_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

    return jsonify({'message': 'Customer added', 'data': data})

@app.route('/api/customers', methods=['GET'])
def get_customers():
    customers = []
    if os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, 'r') as f:
            for line in f:
                customers.append(json.loads(line.strip()))
    return jsonify(customers)

# === DELIVERY BOY ROUTES ===

@app.route('/api/delivery', methods=['POST'])
def add_delivery():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    with open(DELIVERY_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

    return jsonify({'message': 'Delivery boy added', 'data': data})

@app.route('/api/delivery', methods=['GET'])
def get_delivery():
    delivery_boys = []
    if os.path.exists(DELIVERY_FILE):
        with open(DELIVERY_FILE, 'r') as f:
            for line in f:
                delivery_boys.append(json.loads(line.strip()))
    return jsonify(delivery_boys)

# === STATIC FILE ROUTE ===

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

# === ROOT TEST ===

@app.route('/')
def home():
    return '✅ Sirohi Backend is up and running!'

# === DO NOT run app.run() here! Render uses gunicorn ===
@app.route('/api/products', methods=['POST'])
def add_product():
    print("📥 Product upload route hit")
    try:
        data = request.form.to_dict()
        image = request.files.get('image')
        video = request.files.get('video')

        if not image or not video:
            print("❌ Missing image or video")
            return jsonify({'error': 'Both image and video are required'}), 400

        os.makedirs('uploads', exist_ok=True)

        image.save(os.path.join('uploads', image.filename))
        video.save(os.path.join('uploads', video.filename))

        data['image'] = image.filename
        data['video'] = video.filename

        with open('data/products.json', 'a') as f:
            f.write(json.dumps(data) + '\n')

        print("✅ Product saved:", data)
        return jsonify({'message': 'Product saved', 'data': data})

    except Exception as e:
        print("🔥 Upload failed:", str(e))
        return jsonify({'error': str(e)}), 500
