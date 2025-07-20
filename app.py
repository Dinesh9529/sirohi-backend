from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

# Static folders for media
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)

# MongoDB setup
client = MongoClient("mongodb+srv://<USERNAME>:<PASSWORD>@<CLUSTER_URL>/?retryWrites=true&w=majority")
db = client["sirohi"]
products_collection = db["products"]

@app.route('/api/products', methods=['GET'])
def get_products():
    products = list(products_collection.find({}, {'_id': 0}))
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def upload_product():
    data = request.form
    image_file = request.files.get('image')
    video_file = request.files.get('video')

    if not image_file or not video_file:
        return jsonify({"error": "Missing image or video"}), 400

    image_name = image_file.filename
    video_name = video_file.filename

    image_file.save(f"uploads/images/{image_name}")
    video_file.save(f"uploads/videos/{video_name}")

    product = {
        "name": data.get("name"),
        "price": data.get("price"),
        "image": image_name,
        "video": video_name
    }

    products_collection.insert_one(product)
    return jsonify({"message": "Product saved", "data": product})
