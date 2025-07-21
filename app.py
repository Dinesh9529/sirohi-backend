from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://dineshinfrasofttech:<db_password>@sirohi-cluster.rskoyvc.mongodb.net/?retryWrites=true&w=majority&appName=sirohi-cluster")
db = client["sirohi"]
products = db["products"]

@app.route("/")
def home():
    return "Sirohi backend is alive 🔥"

@app.route("/api/products", methods=["GET", "POST"])
def handle_products():
    if request.method == "POST":
        data = request.get_json()
        if data:
            products.insert_one(data)
            return jsonify({"status": "Product added"}), 200
        else:
            return jsonify({"error": "Invalid data"}), 400
    else:
        all_products = list(products.find({}, {"_id": 0}))
        return jsonify(all_products)

if __name__ == "__main__":
    app.run()
