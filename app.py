from flask import Flask, request, jsonify
import os, json

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'data/products.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.form.to_dict()
    image = request.files.get('image')
    video = request.files.get('video')

    if not image or not video:
        return jsonify({'error': 'Both image and video required'}), 400

    # Save media files
    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    video_path = os.path.join(UPLOAD_FOLDER, video.filename)
    image.save(image_path)
    video.save(video_path)

    data['image'] = image.filename
    data['video'] = video.filename

    # Save data to JSON file
    with open(DATA_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

    return jsonify({'message': 'Product saved', 'data': data})

@app.route('/api/products', methods=['GET'])
def get_all():
    products = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            for line in f:
                products.append(json.loads(line.strip()))
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)
