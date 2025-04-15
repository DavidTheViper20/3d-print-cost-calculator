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

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to calculate the 3D model volume (now in mm³)
def calculate_volume(file_path):
    try:
        # Load the 3D model using numpy-stl (only if it's an STL)
        model = mesh.Mesh.from_file(file_path)
        
        # Calculate the volume in mm³ (it will return volume in cubic millimeters)
        volume = model.get_mass_properties()[0]  # This returns the volume in mm³
        return volume
    except Exception as e:
        return None

# Calculate adjusted weight based on infill density
def calculate_weight(volume, infill_density):
    # Model has a perimeter of 0.4mm all around it (walls, roof, and floor)
    perimeter_volume = volume * 0.4  # Assuming perimeter is 40% of the total volume

    # Infill volume is the remaining space inside
    infill_volume = volume - perimeter_volume

    # Adjust the infill volume based on the infill density
    adjusted_infill_volume = infill_volume * infill_density

    # Total volume = perimeter volume + infill volume
    total_adjusted_volume = perimeter_volume + adjusted_infill_volume

    # Calculate weight based on the total adjusted volume (assuming material density = 1g/cm³)
    weight = total_adjusted_volume / 1000  # Convert from mm³ to cm³
    return weight

@app.route('/')
def index():
    return render_template('index.html')  # Render your main page template

@app.route('/test')
def test():
    return 'Flask is working!'  # Simple test route to check Flask

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
        # Calculate volume of the uploaded model
        volume = calculate_volume(file_path)
        if volume is not None:
            return jsonify({'volumeMm3': volume})  # Return volume in mm³
        else:
            return jsonify({'error': 'Failed to calculate volume'})
    return jsonify({'error': 'Invalid file type'})

@app.route('/calculate-cost', methods=['POST'])
def calculate_cost():
    data = request.get_json()
    volumeMm3 = data.get('volumeMm3')
    infillDensity = data.get('infillDensity')  # Getting infill density from the frontend
    layerHeight = data.get('layerHeight')

    if volumeMm3 is None or infillDensity is None or layerHeight is None:
        return jsonify({'error': 'Missing required parameters'})

    # Calculate the adjusted weight based on the volume and infill density
    weightG = calculate_weight(volumeMm3, infillDensity)

    # Cost calculation logic
    material_cost = (weightG * 0.05)  # Material cost based on weight in grams
    time_cost = (volumeMm3 * 0.02) * (1 + (infillDensity - 0.2) * 2) * layerHeight  # Time cost based on mm³
    total_cost = material_cost + time_cost

    return jsonify({
        'material_cost': material_cost,
        'time_cost': time_cost,
        'total_cost': total_cost,
        'weightG': weightG  # Return the adjusted weight
    })

if __name__ == '__main__':
    app.run(debug=True)
