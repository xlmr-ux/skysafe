from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import boto3
import os

app = Flask(__name__)

# Key for encryption/decryption
SECRET_KEY = Fernet.generate_key()
cipher = Fernet(SECRET_KEY)

# AWS S3 Configuration
AWS_BUCKET_NAME = "localsinghsavvy"
AWS_ACCESS_KEY = "AKIAQYEI45XCXQ3EY27P"
AWS_SECRET_KEY = "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"
AWS_REGION = "us-east-1"

s3_client = boto3.client(
    's3',
    aws_access_key_id=AKIAQYEI45XCXQ3EY27P,
    aws_secret_access_key=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,
    region_name=us-east-1
)

# Upload folder for temporary storage
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


# Upload to AWS S3
@app.route('/upload/aws', methods=['POST'])
def upload_to_aws():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        s3_client.upload_file(file_path, AWS_BUCKET_NAME, file.filename)
    except Exception as e:
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500

    return jsonify({"message": f"File uploaded to AWS S3: {file.filename}"})


if __name__ == '__main__':
    app.run(debug=True)
