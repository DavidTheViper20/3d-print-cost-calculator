from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import zipfile
from io import BytesIO
import numpy as np
from stl import mesh
import datetime
import smtplib
from email.message import EmailMessage

# Initialize the Flask app
app = Flask(__name__)

# Set up folders
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = os.path.join('static', 'downloads')
ALLOWED_EXTENSIONS = {'stl', 'obj'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# 📩 Send ZIP file via email
def send_zip_file_via_email(zip_path, zip_id):
    sender_email = 'ultifab23@gmail.com'
    receiver_email = 'ultifab23@gmail.com'
    sender_password = 'kmux dtuk peey ebdp'  # 🔁 Replace with your Gmail app password

    msg = EmailMessage()
    msg['Subject'] = f'New 3D Print Quote - {zip_id}'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(f'A new quote has been generated.\n\nQuote ID: {zip_id}\nSee attached ZIP file.')

    with open(zip_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='zip', filename=f'{zip_id}.zip')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print(f"[✅] Email sent with attachment {zip_id}.zip")
    except Exception as e:
        print(f"[❌] Failed to send email: {e}")

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to calculate the 3D model volume (now in mm³)
def calculate_volume(file_path):
    try:
        model = mesh.Mesh.from_file(file_path)
        volume = model.get_mass_properties()[0]
        return volume
    except Exception as e:
        return None

# Calculate adjusted weight based on infill density
def calculate_weight(volume, infill_density):
    perimeter_volume = volume * 0.4
    infill_volume = volume - perimeter_volume
    adjusted_infill_volume = infill_volume * infill_density
    total_adjusted_volume = perimeter_volume + adjusted_infill_volume
    weight = total_adjusted_volume / 1000
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

@app.route('/generate_zip', methods=['POST'])
def generate_zip():
    if 'stlFile' not in request.files:
        return jsonify({"error": "No STL file provided"}), 400

    stl_file = request.files['stlFile']
    stl_filename = secure_filename(stl_file.filename)
    stl_name = os.path.splitext(stl_filename)[0]

    # Collect form data
    material = request.form.get("material", "N/A")
    colour = request.form.get("colour", "N/A")
    infill = request.form.get("infill", "N/A")
    quantity = request.form.get("quantity", "N/A")
    cost = request.form.get("totalCost", "N/A")
    wall = request.form.get("wallLayers", "N/A")
    top_bottom = request.form.get("topBottomLayers", "N/A")
    layer = request.form.get("layerHeight", "N/A")
    notes = request.form.get("notes", "N/A")

    build_text = f"""Material: {material}
Colour: {colour}
Infill Density: {infill}%
Quantity: {quantity}
Total Cost: ${cost}
Wall Layers: {wall}
Top/Bottom Layers: {top_bottom}
Layer Height: {layer}
Notes: {notes}
"""

    # Format cost and filename
    formatted_cost = cost.replace('.', '') if cost != "N/A" else "N_A"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    zip_id = f"3DModel{formatted_cost}{timestamp}"
    zip_filename = f"{zip_id}.zip"
    zip_path = os.path.join(DOWNLOAD_FOLDER, zip_filename)
    print(f"ZIP file will be saved at: {zip_path}")

    # Create the ZIP file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        stl_data = stl_file.read()
        zipf.writestr(f"{stl_name}.stl", stl_data)  # Write the STL file
        zipf.writestr("build_parameters.txt", build_text)  # Write parameters

    # ✅ Send ZIP file by email
    send_zip_file_via_email(zip_path, zip_id)

    return jsonify({"filename": zip_id})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
