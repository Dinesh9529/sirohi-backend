from flask import Flask, request, jsonify

app = Flask(__name__)
products = []

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    products.append(data)
    return jsonify({"message": "Product added", "data": data})

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

app.run(debug=True)
