from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import traceback

app = Flask(__name__)
CORS(app)

# 🔒 Redirect HTTP to HTTPS
@app.before_request
def redirect_to_https():
    if request.headers.get("X-Forwarded-Proto", "http") == "http":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

# 📂 Upload folder setup
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB limit

# ✅ Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🔐 MongoDB client (Standard URI from environment)
def get_db_collection():
    uri = os.environ.get("DB_URL")
    if not uri or not uri.startswith("mongodb"):
        raise ValueError(f"❌ Invalid MongoDB URI: {repr(uri)}")
    print("✅ MongoDB URI loaded:", repr(uri))
    client = MongoClient(
        uri,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    db = client["sirohi"]
    return db["products"]

@app.route("/")
def home():
    return "Sirohi backend is alive 🔥"

@app.route("/uploads/<filename>")
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/ping-db")
def ping_db():
    try:
        get_db_collection().find_one()
        return jsonify({"status": "MongoDB Connected ✅"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/products", methods=["GET", "POST"])
def upload_product():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        main_image = request.files.get("image")
        gallery_files = request.files.getlist("gallery_images")

        if not name or not price or not main_image:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            main_filename = secure_filename(main_image.filename)
            main_image.save(os.path.join(app.config["UPLOAD_FOLDER"], main_filename))

            gallery_urls = []
            for file in gallery_files:
                if file and file.filename.strip():
                    if allowed_file(file.filename):
                        gallery_filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config["UPLOAD_FOLDER"], gallery_filename))
                        gallery_urls.append(f"/uploads/{gallery_filename}")

            product = {
                "name": name,
                "price": price,
                "main_image_url": f"/uploads/{main_filename}",
                "gallery_urls": gallery_urls
            }
            get_db_collection().insert_one(product)

            return jsonify({"status": "Product uploaded", "product": product}), 200

        except Exception as e:
            print("Upload error:", str(e))
            traceback.print_exc()
            return jsonify({"error": "Upload failed", "details": str(e)}), 500

    else:
        try:
            products = list(get_db_collection().find({}, {"_id": 0}))
            return jsonify(products)
        except Exception as e:
            print("DB fetch error:", str(e))
            traceback.print_exc()
            return jsonify({"error": "DB fetch failed", "details": str(e)}), 500
