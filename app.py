
if not os.path.exists("uploads"):
    os.makedirs("uploads")

Stashed changes
from flask import Flask, request, jsonify, send_from_directory, redirect, session, Blueprint
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern
from werkzeug.utils import secure_filename
import os
import logging
import traceback

app = Flask(__name__)
app.secret_key = 'sirohi_secret_key'
CORS(app)

logging.basicConfig(level=logging.INFO)

@app.before_request
def redirect_to_https():
    if request.headers.get("X-Forwarded-Proto", "http") == "http":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if not file or not allowed_file(file.filename):
        return ""
    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    return f"/uploads/{filename}"

def get_db_collection():
    uri = os.environ.get("DB_URL")
    if not uri or not uri.startswith("mongodb"):
        raise ValueError(f"❌ Invalid MongoDB URI: {repr(uri)}")

    logging.info("✅ MongoDB URI loaded: %s", repr(uri))

    client = MongoClient(
        uri,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=10000
    )
    db = client["sirohi"]
    return db["products"]

@app.route("/")
def home():
    return "Sirohi backend is alive 🔥"

@app.route("/uploads/<filename>")
def serve_file(filename):
    if not allowed_file(filename):
        return jsonify({"error": "Invalid file type"}), 403
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/ping-db")
def ping_db():
    try:
        get_db_collection().find_one()
        return jsonify({"status": "MongoDB Connected ✅"})
    except Exception as e:
        logging.error("Ping DB Error: %s", str(e), exc_info=True)
        return jsonify({"error": str(e)})

@app.route('/vendor/products', methods=['GET'])
def vendor_products():
    vendor_id = session.get('vendor_id')
    if not vendor_id:
        return jsonify({"error": "Vendor not logged in"}), 401

    try:
        products = []
        cursor = get_db_collection().find(
            {"vendor_id": vendor_id},
            {"_id": 0, "vendor_id": 0}
        )
        for item in cursor:
            products.append(item)
        return jsonify({"products": products})
    except Exception as e:
        logging.error("Vendor product fetch failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to fetch vendor products"}), 500

@app.route("/api/products", methods=["GET", "POST"])
def upload_product():
    if request.method == "POST":
        if request.content_type is None or "multipart/form-data" not in request.content_type:
            return jsonify({"error": "Invalid content-type"}), 400

        name = request.form.get("name")
        price = request.form.get("price")
        vendor_id = request.form.get("vendor_id") or session.get("vendor_id")
        category = request.form.get("category")
        main_image = request.files.get("image")
        gallery_files = request.files.getlist("gallery_images")

        if not name or not price or not main_image or not category:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            price = float(price)
        except ValueError:
            return jsonify({"error": "Invalid price format"}), 400

        extra_fields = {}
        if category == "kirana":
            weight = request.form.get("weight")
            try:
                extra_fields["weight"] = float(weight) if weight else None
            except ValueError:
                return jsonify({"error": "Invalid weight value"}), 400

        elif category == "kapda":
            extra_fields["size"] = request.form.get("size")
            try:
                extra_fields["waist"] = int(request.form.get("waist")) if request.form.get("waist") else None
                extra_fields["length"] = int(request.form.get("length")) if request.form.get("length") else None
            except ValueError:
                return jsonify({"error": "Invalid size values"}), 400

        stock_data = {}
        try:
            stock_qty = request.form.get("stockQty")
            stock_size = request.form.get("stockSize")
            stock_liter = request.form.get("stockLiter")
            stock_kg = request.form.get("stockKg")

            stock_data = {
                "qty": int(stock_qty) if stock_qty else None,
                "size": stock_size,
                "liter": float(stock_liter) if stock_liter else None,
                "kg": float(stock_kg) if stock_kg else None
            }
        except ValueError:
            return jsonify({"error": "Invalid stock values"}), 400

        try:
            main_url = save_file(main_image)
            gallery_urls = [save_file(f) for f in gallery_files if f and f.filename.strip()]

            product = {
                "name": name,
                "price": price,
                "main_image_url": main_url,
                "gallery_urls": gallery_urls,
                "vendor_id": vendor_id,
                "category": category,
                "stock": stock_data,
                **extra_fields
            }

            collection = get_db_collection().with_options(write_concern=WriteConcern("majority"))
            result = collection.insert_one(product)
            product["_id"] = str(result.inserted_id)

            return jsonify({"status": "Product uploaded", "product": product}), 200

        except Exception as e:
            logging.error("Upload failed: %s", str(e), exc_info=True)
            return jsonify({"error": "Upload failed", "details": str(e)}), 500

    else:
        try:
            vendor_filter = request.args.get("vendor_id")
            query = {"vendor_id": vendor_filter} if vendor_filter else {}

            products = []
            for item in get_db_collection().find(query):
                item["_id"] = str(item["_id"])
                products.append(item)
            return jsonify(products)
        except Exception as e:
            logging.error("DB fetch failed: %s", str(e), exc_info=True)
            return jsonify({"error": "DB fetch failed", "details": str(e)}), 500

@app.route("/api/service-products", methods=["GET"])
def service_products():
    category = request.args.get("category")
    if not category:
        return jsonify({"error": "Category required"}), 400

    try:
        products = []
        cursor = get_db_collection().find(
            {"category": category},
            {"_id": 0, "vendor_id": 0}
        )
        for item in cursor:
            products.append(item)
        return jsonify({"products": products})
    except Exception as e:
        logging.error("Service products fetch failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Service fetch failed", "details": str(e)}), 500

# ✅ Admin Panel Routes (Added Safely Below Existing Code)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
def dashboard():
    return jsonify({
        "vendors": 42,
        "orders": 128,
        "earnings": 56000
    })

@admin_bp.route('/vendors', methods=['GET'])
def get_all_vendors():
    try:
        db = MongoClient(os.environ.get("DB_URL")).sirohi
        vendors = list(db.vendors.find({}, {"_id": 0}))
        return jsonify(vendors)
    except Exception as e:
        logging.error("Vendor fetch failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to fetch vendors"}), 500

@admin_bp.route('/approve-vendor/<vendor_id>', methods=['POST'])
def approve_vendor(vendor_id):
    try:
        db = MongoClient(os.environ.get("DB_URL")).sirohi
        db.vendors.update_one({"_id": vendor_id}, {"$set": {"approved": True}})
        return jsonify({"status": "Vendor approved"})
    except Exception as e:
        logging.error("Vendor approval failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Approval failed"}), 500
@admin_bp.route('/delete-vendor/<vendor_id>', methods=['DELETE'])
def delete_vendor(vendor_id):
    try:
        db = MongoClient(os.environ.get("DB_URL")).sirohi
        db.vendors.delete_one({"_id": vendor_id})
        return jsonify({"status": "Vendor deleted"})
    except Exception as e:
        logging.error("Vendor delete failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Delete failed"}), 500
app.register_blueprint(admin_bp)

from bson import ObjectId
# ✅ Place this at the top of app.py
client = MongoClient(os.environ.get("DB_URL"))
db = client.sirohi

# ✅ Then use this route
@app.route("/api/register-vendor", methods=["POST"])
def register_vendor():
    try:
        data = request.get_json()
        required = ["name", "category", "price"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing vendor fields"}), 400

        vendor = {
            "name": data["name"],
            "category": data["category"],
            "price": data["price"],
            "approved": False,
            "created_at": datetime.utcnow()
        }
        result = db.vendors.insert_one(vendor)
        vendor["_id"] = str(result.inserted_id)
        return jsonify({"status": "Vendor registered", "vendor": vendor})
    except Exception as e:
        logging.error("Vendor registration failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Vendor registration failed"}), 500


@app.route("/api/register-customer", methods=["POST"])
def register_customer():
    try:
        data = request.get_json()
        required = ["name", "mobile", "address"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing customer fields"}), 400

        db = MongoClient(os.environ.get("DB_URL")).sirohi
        customer = {
            "name": data["name"],
            "mobile": data["mobile"],
            "address": data["address"],
            "created_at": datetime.utcnow()
        }
        result = db.customers.insert_one(customer)
        customer["_id"] = str(result.inserted_id)
        return jsonify({"status": "Customer registered", "customer": customer})
    except Exception as e:
        logging.error("Customer registration failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Customer registration failed"}), 500


@app.route("/api/register-delivery", methods=["POST"])
def register_delivery_boy():
    try:
        data = request.get_json()
        required = ["name", "location", "mobile"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing delivery boy fields"}), 400

        db = MongoClient(os.environ.get("DB_URL")).sirohi
        delivery = {
            "name": data["name"],
            "location": data["location"],
            "mobile": data["mobile"],
            "active": True,
            "created_at": datetime.utcnow()
        }
        result = db.delivery.insert_one(delivery)
        delivery["_id"] = str(result.inserted_id)
        return jsonify({"status": "Delivery boy registered", "delivery": delivery})
    except Exception as e:
        logging.error("Delivery registration failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Delivery registration failed"}), 500


@app.route("/api/paid-plans", methods=["GET"])
def get_paid_plans():
    try:
        db = MongoClient(os.environ.get("DB_URL")).sirohi
        plans = list(db.plans.find({}, {"_id": 0}))
        return jsonify({"plans": plans})
    except Exception as e:
        logging.error("Paid plans fetch failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to fetch plans"}), 500


@app.route("/api/subscribe-plan", methods=["POST"])
def subscribe_plan():
    try:
        data = request.get_json()
        required = ["customer_id", "plan_id"]
        if not all(k in data for k in required):
            return jsonify({"error": "Missing subscription fields"}), 400

        db = MongoClient(os.environ.get("DB_URL")).sirohi
        subscription = {
            "customer_id": data["customer_id"],
            "plan_id": data["plan_id"],
            "subscribed_at": datetime.utcnow()
        }
        result = db.subscriptions.insert_one(subscription)
        subscription["_id"] = str(result.inserted_id)
        return jsonify({"status": "Plan subscribed", "subscription": subscription})
    except Exception as e:
        logging.error("Subscription failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Subscription failed"}), 500

 Updated upstream





Stashed changes
from werkzeug.utils import secure_filename
from datetime import datetime


# ✅ Customer Registration
@app.route("/api/register-customer", methods=["POST"])
def register_customer():
    try:
        data = request.get_json()
        customer = {
            "name": data["name"],
            "mobile": data["mobile"],
            "address": data["address"],
            "created_at": datetime.utcnow()
        }
        result = db.customers.insert_one(customer)
        customer["_id"] = str(result.inserted_id)
        return jsonify({"status": "Customer registered", "customer": customer})
    except Exception as e:
        return jsonify({"error": "Customer registration failed"}), 500

# ✅ Delivery Boy Registration
@app.route("/api/register-delivery", methods=["POST"])
def register_delivery():
    try:
        data = request.get_json()
        delivery = {
            "name": data["name"],
            "location": data["location"],
            "mobile": data["mobile"],
            "active": True,
            "created_at": datetime.utcnow()
        }
        result = db.delivery.insert_one(delivery)
        delivery["_id"] = str(result.inserted_id)
        return jsonify({"status": "Delivery boy registered", "delivery": delivery})
    except Exception as e:
        return jsonify({"error": "Delivery registration failed"}), 500

# ✅ Product Upload
@app.route("/api/upload-product", methods=["POST"])
def upload_product():
    try:
        name = request.form["name"]
        category = request.form["category"]
        price = float(request.form["price"])
        vendor_id = request.form["vendor_id"]
        stock_qty = int(request.form["stockQty"])
        stock_liter = float(request.form["stockLiter"])

        main_image = request.files["main_image"]
        filename = secure_filename(main_image.filename)
        main_image.save(os.path.join("uploads", filename))

        product = {
            "name": name,
            "category": category,
            "price": price,
            "vendor_id": vendor_id,
            "main_image_url": f"/uploads/{filename}",
            "stock": {"qty": stock_qty, "liter": stock_liter},
            "created_at": datetime.utcnow()
        }
        result = db.products.insert_one(product)
        product["_id"] = str(result.inserted_id)
        return jsonify({"status": "Product uploaded", "product": product})
    except Exception as e:
        return jsonify({"error": "Product upload failed"}), 500

@app.route("/api/subscribe-plan", methods=["POST"])
def subscribe_plan():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        required_fields = ["customer_id", "plan_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        subscription = {
            "customer_id": data["customer_id"],
            "plan_id": data["plan_id"],
            "subscribed_at": datetime.utcnow()
        }
        result = db.subscriptions.insert_one(subscription)
        subscription["_id"] = str(result.inserted_id)
        return jsonify({"status": "Plan subscribed", "subscription": subscription})
    except Exception as e:
        logging.error("Subscription failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Subscription failed"}), 500


# ✅ Paid Plans
@app.route("/api/paid-plans", methods=["GET"])
def get_paid_plans():
    try:
        plans = list(db.plans.find({}, {"_id": 0}))
        return jsonify({"plans": plans})
    except Exception as e:
        return jsonify({"error": "Failed to fetch plans"}), 500
