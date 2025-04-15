from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import numpy as np
from stl import mesh

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'stl', 'obj'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_volume(file_path):
    try:
        model = mesh.Mesh.from_file(file_path)
        volume = model.get_mass_properties()[0]
        return volume
    except Exception:
        return None

def calculate_weight(volume, infill_density):
    perimeter_volume = volume * 0.4
    infill_volume = volume - perimeter_volume
    adjusted_infill_volume = infill_volume * infill_density
    total_adjusted_volume = perimeter_volume + adjusted_infill_volume
    weight = total_adjusted_volume / 1000
    return weight

@app.after_request
def add_headers(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return 'Flask is working!'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        volume = calculate_volume(file_path)
        if volume is not None:
            return jsonify({'volumeMm3': volume})
        else:
            return jsonify({'error': 'Failed to calculate volume'})
    return jsonify({'error': 'Invalid file type'})

@app.route('/calculate-cost', methods=['POST'])
def calculate_cost():
    data = request.get_json()
    volumeMm3 = data.get('volumeMm3')
    infillDensity = data.get('infillDensity')
    layerHeight = data.get('layerHeight')

    if volumeMm3 is None or infillDensity is None or layerHeight is None:
        return jsonify({'error': 'Missing required parameters'})

    weightG = calculate_weight(volumeMm3, infillDensity)

    material_cost = (weightG * 0.05)
    time_cost = (volumeMm3 * 0.02) * (1 + (infillDensity - 0.2) * 2) * layerHeight
    total_cost = material_cost + time_cost

    return jsonify({
        'material_cost': material_cost,
        'time_cost': time_cost,
        'total_cost': total_cost,
        'weightG': weightG
    })

if __name__ == '__main__':
    app.run(debug=True)
