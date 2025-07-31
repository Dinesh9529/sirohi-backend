from flask import Flask, request, jsonify, send_from_directory, redirect, session
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

        # Category-specific fields
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
