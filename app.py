from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

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

    if not image_file:
        return jsonify({"error": "No image uploaded"}), 400

    image_filename = image_file.filename
    image_file.save(f"uploads/{image_filename}")

    product = {
        "name": data.get("name"),
        "price": data.get("price"),
        "video": data.get("video_link"),
        "image": image_filename
    }

    products_collection.insert_one(product)
    return jsonify({"message": "Product saved", "data": product})
