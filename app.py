from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
import qrcode
from base64 import b64encode, b64decode
from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa
from PyPDF2 import PdfFileReader, PdfFileWriter
from PIL import Image
from pyzbar.pyzbar import decode

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
SIGNATURE_FOLDER = 'signatures'
QR_CODE_FOLDER = 'static/qr_codes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SIGNATURE_FOLDER'] = SIGNATURE_FOLDER
app.config['QR_CODE_FOLDER'] = QR_CODE_FOLDER

# Pastikan folder upload, signature, dan qr_codes ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SIGNATURE_FOLDER, exist_ok=True)
os.makedirs(QR_CODE_FOLDER, exist_ok=True)

# Generate a key pair for demonstration
key = ECC.generate(curve='Ed25519')
pub_key = key.public_key()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sign', methods=['GET', 'POST'])
def sign_pdf():
    if request.method == 'POST':
        name = request.form['name']
        file = request.files['file']
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Baca konten PDF
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        # Buat signature
        signer = eddsa.new(key, 'rfc8032')
        signature = signer.sign(pdf_content)
        signature_b64 = b64encode(signature).decode('utf-8')
        
        # Simpan QR code
        qr = qrcode.QRCode()
        qr.add_data(signature_b64)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        qr_filename = f'{name}_qr.png'
        qr_path = os.path.join(app.config['QR_CODE_FOLDER'], qr_filename)
        img.save(qr_path)
        
        return render_template('sign.html', signature=signature_b64, qr_code=qr_filename)
    return render_template('sign.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify_pdf():
    if request.method == 'POST':
        method = request.form.get('method')
        if method == 'code':
            signature_b64 = request.form.get('signature')
            signature = b64decode(signature_b64)
        elif method == 'qr':
            file = request.files['file']
            filename = secure_filename(file.filename)
            qr_path = os.path.join(app.config['SIGNATURE_FOLDER'], filename)
            file.save(qr_path)
            
            # Membaca QR code
            img = Image.open(qr_path)
            decoded_objs = decode(img)
            if len(decoded_objs) == 0:
                return jsonify({'status': 'invalid', 'message': 'QR code tidak valid'}), 400
            
            signature_b64 = decoded_objs[0].data.decode('utf-8')
            signature = b64decode(signature_b64)
        
        filename = request.form.get('filename')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        verifier = eddsa.new(pub_key, 'rfc8032')
        try:
            verifier.verify(pdf_content, signature)
            return jsonify({'status': 'valid', 'filename': filename})
        except ValueError:
            return jsonify({'status': 'invalid'}), 400
    return render_template('verify.html')

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/preview/<path:filename>', methods=['GET'])
def preview_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
