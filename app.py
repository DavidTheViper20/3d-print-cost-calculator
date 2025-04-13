from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import numpy as np
from stl import mesh

# Initialize the Flask app
app = Flask(__name__)

# Set up a folder to store uploaded files
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'stl', 'obj'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Simulated cart for this example (in production you'd use a session or database)
cart = []

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to calculate the 3D model volume (in mm³)
def calculate_volume(file_path):
    try:
        # Load the 3D model using numpy-stl (only if it's an STL)
        model = mesh.Mesh.from_file(file_path)
        volume = model.get_mass_properties()[0]  # Returns volume in mm³
        return volume
    except Exception as e:
        print(f"Error calculating volume: {e}")
        return None

# Function to calculate adjusted weight based on infill density
def calculate_weight(volume, infill_density):
    # Assume perimeter is 40% of total volume
    perimeter_volume = volume * 0.4
    infill_volume = volume - perimeter_volume
    adjusted_infill_volume = infill_volume * infill_density
    total_adjusted_volume = perimeter_volume + adjusted_infill_volume
    weight = total_adjusted_volume / 1000  # Convert mm³ to cm³
    return weight

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

    # Cost calculation logic
    material_cost = (weightG * 0.05)
    time_cost = (volumeMm3 * 0.02) * (1 + (infillDensity - 0.2) * 2) * layerHeight
    total_cost = material_cost + time_cost

    return jsonify({
        'material_cost': material_cost,
        'time_cost': time_cost,
        'total_cost': total_cost,
        'weightG': weightG
    })

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    material = data.get('material')
    colour = data.get('colour')
    quantity = data.get('quantity')
    total_cost = data.get('total_cost')

    if not all([material, colour, quantity, total_cost]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Add product to cart (this is a simulated cart for now)
    cart_item = {
        'material': material,
        'colour': colour,
        'quantity': quantity,
        'total_cost': total_cost
    }
    cart.append(cart_item)

    return jsonify({'message': 'Product added to cart', 'cart': cart})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
