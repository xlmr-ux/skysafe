from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import boto3
from google.cloud import storage
import os

app = Flask(__name__)

# Key for encryption/decryption
SECRET_KEY = Fernet.generate_key()
cipher = Fernet(SECRET_KEY)

# Upload folders
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Encrypt file
@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    with open(file_path, 'rb') as f:
        encrypted_data = cipher.encrypt(f.read())

    encrypted_path = f"{file_path}.enc"
    with open(encrypted_path, 'wb') as f:
        f.write(encrypted_data)

    return jsonify({"message": "File encrypted successfully", "path": encrypted_path})


# Decrypt file
@app.route('/decrypt', methods=['POST'])
def decrypt_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    with open(file_path, 'rb') as f:
        decrypted_data = cipher.decrypt(f.read())

    decrypted_path = file_path.replace('.enc', '')
    with open(decrypted_path, 'wb') as f:
        f.write(decrypted_data)

    return jsonify({"message": "File decrypted successfully", "path": decrypted_path})


# Upload to Google Cloud Storage
@app.route('/upload/google', methods=['POST'])
def upload_to_google():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    bucket_name = "your-google-cloud-bucket"
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)

    return jsonify({"message": f"File uploaded to Google Cloud: {file.filename}"})


# Upload to AWS S3
@app.route('/upload/aws', methods=['POST'])
def upload_to_aws():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    bucket_name = "your-aws-s3-bucket"

    s3_client = boto3.client('s3')
    s3_client.upload_fileobj(file, bucket_name, file.filename)

    return jsonify({"message": f"File uploaded to AWS S3: {file.filename}"})


if __name__ == '__main__':
    app.run(debug=True)