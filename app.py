from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import traceback  # ✅ Global import for cleaner exception blocks

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Upload folder config
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ✅ MongoDB lazy client (fork-safe for Gunicorn)
def get_db_collection():
    client = MongoClient(
        "mongodb+srv://dineshinfrasofttech:<db_password>@sirohi-cluster.rskoyvc.mongodb.net/?retryWrites=true&w=majority&appName=sirohi-cluster",
        tlsAllowInvalidCertificates=True
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
            # Save main image
            main_filename = secure_filename(main_image.filename)
            main_path = os.path.join(app.config["UPLOAD_FOLDER"], main_filename)
            main_image.save(main_path)

            # Save gallery images
            gallery_paths = []
            for file in gallery_files:
                if file and file.filename:
                    gallery_filename = secure_filename(file.filename)
                    gallery_path = os.path.join(app.config["UPLOAD_FOLDER"], gallery_filename)
                    file.save(gallery_path)
                    gallery_paths.append(gallery_path)

            # Store product in DB
            product = {
                "name": name,
                "price": price,
                "main_image": main_path,
                "gallery": gallery_paths
            }
            get_db_collection().insert_one(product)
            return jsonify({"status": "Product uploaded", "product": product}), 200

        except Exception as e:
            traceback.print_exc()  # ✅ Logs full error in Render console
            return jsonify({"error": f"Upload failed: {str(e)}"}), 500

    else:
        try:
            all_data = list(get_db_collection().find({}, {"_id": 0}))
            return jsonify(all_data)
        except Exception as e:
            traceback.print_exc()  # ✅ Add traceback here too for GET errors
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
