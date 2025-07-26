from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import traceback
from dotenv import load_dotenv

# ✅ Load environment variables from .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# 📂 Upload folder setup
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB file size limit

# 🔐 MongoDB client with TLS settings
def get_db_collection():
    uri = os.getenv("MONGO_URI")
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
            # 🖼️ Save main image
            main_filename = secure_filename(main_image.filename)
            main_path = os.path.join(app.config["UPLOAD_FOLDER"], main_filename)
            main_image.save(main_path)

            # 🖼️ Save gallery images
            gallery_paths = []
            for file in gallery_files:
                if file and file.filename:
                    gallery_filename = secure_filename(file.filename)
                    gallery_path = os.path.join(app.config["UPLOAD_FOLDER"], gallery_filename)
                    file.save(gallery_path)
                    gallery_paths.append(gallery_path)

            # 🧾 Store product in DB
            product = {
                "name": name,
                "price": price,
                "main_image": main_path,
                "gallery": gallery_paths
            }
            get_db_collection().insert_one(product)
            return jsonify({"status": "Product uploaded", "product": product}), 200

        except Exception:
            traceback.print_exc()
            return jsonify({"error": "Upload failed"}), 500

    else:
        try:
            all_data = list(get_db_collection().find({}, {"_id": 0}))
            return jsonify(all_data)
        except Exception:
            traceback.print_exc()
            return jsonify({"error": "DB fetch failed"}), 500

# ⛔️ No app.run() needed for deployment (Gunicorn handles it)
