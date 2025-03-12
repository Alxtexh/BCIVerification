import requests
import json
import os

def load_institutions(file_path="institutions.json"):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return []

def save_institutions(institutions, file_path="institutions.json"):
    with open(file_path, "w") as file:
        json.dump(institutions, file)

def load_certificates(file_path="certificates.json"):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return []

def save_certificates(certificates, file_path="certificates.json"):
    with open(file_path, "w") as file:
        json.dump(certificates, file)

def is_duplicate_registration_no(certificates, registration_no):
    for cert in certificates:
        if cert["registration_no"] == registration_no:
            return True
    return False

def is_duplicate_email(certificates, email):
    for cert in certificates:
        if cert["email"] == email:
            return True
    return False

def delete_certificate(certificates, registration_no, email):
    certificates = [cert for cert in certificates if cert["registration_no"] != registration_no and cert["email"] != email]
    return certificates

def delete_from_pinata(ipfs_hash, api_key, api_secret):
    url = f"https://api.pinata.cloud/pinning/unpin/{ipfs_hash}"
    headers = {
        "pinata_api_key": api_key,
        "pinata_secret_api_key": api_secret,
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        return False

def clear_certificates():
    """Clear all stored certificates"""
    certificates_file = os.path.join("..", "data", "certificates.json")
    try:
        with open(certificates_file, "w") as f:
            json.dump([], f)
        return True
    except Exception as e:
        print(f"Error clearing certificates: {e}")
        return False