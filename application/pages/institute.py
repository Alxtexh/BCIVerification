import streamlit as st
import requests
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import hashlib
from utils.cert_utils import generate_certificate_pdf  # Updated import
from utils.streamlit_utils import view_certificate, displayPDF, hide_icons, hide_sidebar, remove_whitespaces
from connection import contract, w3
from streamlit_extras.switch_page_button import switch_page
from utils.file_utils import load_institutions, save_institutions, load_certificates, save_certificates, is_duplicate_registration_no, is_duplicate_email, delete_certificate, delete_from_pinata
import pandas as pd
import time
from docx import Document
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
from functools import lru_cache
import asyncio
import gc
from PIL import Image
import shutil
import logging
from datetime import datetime  # Import datetime module

st.set_page_config(
    page_title="Institute",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)
hide_icons()
hide_sidebar()
remove_whitespaces()

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'institutions' not in st.session_state:
    st.session_state.institutions = load_institutions()
if 'selected_institution' not in st.session_state:
    st.session_state.selected_institution = None
if 'certificates' not in st.session_state:
    st.session_state.certificates = load_certificates()
if 'refresh' not in st.session_state:
    st.session_state.refresh = False

# Check if the user is logged in and has the correct profile
if not st.session_state.logged_in or st.session_state.profile != "Institute":
    st.error("Access denied. This page is only for Institute users.")
    switch_page("app")
    st.stop()  # Stop execution to prevent further errors

load_dotenv()

api_key = os.getenv("PINATA_API_KEY")
api_secret = os.getenv("PINATA_API_SECRET")
email_user = os.getenv("EMAIL_USER")
email_password = os.getenv("EMAIL_PASSWORD")

# Ensure API keys are loaded
if not api_key or not api_secret:
    st.error("Pinata API keys are not set. Please check your environment variables.")
    st.stop()

def upload_to_pinata(file_path, api_key, api_secret, max_retries=3):
    """
    Upload file to Pinata with retry logic
    """
    # Configure retry strategy
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504],
    )
    
    # Create session with retry strategy
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    
    pinata_api_url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": api_key,
        "pinata_secret_api_key": api_secret,
    }

    try:
        with open(file_path, "rb") as file:
            files = {"file": file}
            
            for attempt in range(max_retries):
                try:
                    response = session.post(
                        pinata_api_url, 
                        headers=headers, 
                        files=files, 
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    if "IpfsHash" in result:
                        return result["IpfsHash"]
                    
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        st.error(f"Failed to upload after {max_retries} attempts: {str(e)}")
                        return None
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
    except Exception as e:
        st.error(f"Error preparing file upload: {str(e)}")
        return None

def send_email(to_email, certificate_id, download_link):
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = to_email
    msg['Subject'] = "Certificate Issued"

    body = f"Dear Student,\n\nCongratulations on completing your Course. Here are your certificate details: \n\nCertificate ID: {certificate_id}\nDownload Link: {download_link}\n\nBest regards,\n {st.session_state.selected_institution}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, to_email, text)
        server.quit()
        return "Email sent successfully"
    except Exception as e:
        return f"Failed to send email: {e}"

def delete_from_pinata(ipfs_hash, api_key, api_secret):
    url = f"https://api.pinata.cloud/pinning/unpin/{ipfs_hash}"
    headers = {
        "pinata_api_key": api_key,
        "pinata_secret_api_key": api_secret
    }
    response = requests.delete(url, headers=headers)
    return response.status_code == 200

def read_docx(file):
    doc = Document(file)
    data = []
    keys = None
    for i, table in enumerate(doc.tables):
        for row in table.rows:
            text = (cell.text for cell in row.cells)
            if i == 0 and keys is None:
                keys = tuple(text)
                continue
            row_data = dict(zip(keys, text))
            data.append(row_data)
    return pd.DataFrame(data)

def normalize_column_names(df):
    # Ensure all column names are strings
    df.columns = df.columns.map(str)
    # Convert all column names to strings explicitly
    df.columns = df.columns.astype(str)
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

def map_columns(df):
    column_mapping = {
        'registration_no': 'Registration No',
        'full_name': 'Full Name',
        'course': 'Course',
        'email': 'Email'
    }
    # Create a reverse mapping for normalization
    reverse_mapping = {v.lower().replace(' ', '_'): k for k, v in column_mapping.items()}
    # Rename columns based on the reverse mapping
    df = df.rename(columns=reverse_mapping)
    return df

def handle_transaction(contract_function):
    try:
        tx_hash = contract_function.transact({
            'from': w3.eth.accounts[0],  # Ensure the sender's address is included
            'gas': 2000000
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        # Log the transaction receipt
        print(f"Transaction receipt: {receipt}")
        return receipt
    except Exception as e:
        st.error(f"Transaction failed: {str(e)}")
        return None

@lru_cache(maxsize=1)
def load_certificate_template():
    return Image.open(os.path.join("..", "assets", "certificate_template.pdf"))

# Add this function before the process_certificate function

def generate_file_path(registration_no):
    """Generate a safe file path for certificate storage"""
    # Create safe filename by replacing special characters
    safe_filename = f"{registration_no.replace('/', '_').replace('\\', '_')}.pdf"
    # Create the certificates directory if it doesn't exist
    certificates_dir = os.path.join("..", "application", "certificates")
    os.makedirs(certificates_dir, exist_ok=True)
    # Return the complete file path
    return os.path.join(certificates_dir, safe_filename)

import time  # Import time module for delay

def revoke_certificate(certificate_id):
    try:
        # Find the certificate details
        certificate = next((cert for cert in st.session_state.certificates if cert['certificate_id'] == certificate_id), None)
        if not certificate:
            st.error("Invalid Certificate ID.")
            return False

        # Revoke the certificate on the blockchain
        tx_receipt = handle_transaction(contract.functions.invalidateCertificate(certificate_id))
        if tx_receipt:
            # Remove from local storage
            st.session_state.certificates = [cert for cert in st.session_state.certificates if cert['certificate_id'] != certificate_id]
            save_certificates(st.session_state.certificates)

            # Delete from Pinata
            if delete_from_pinata(certificate['ipfsHash'], api_key, api_secret):
                st.success("Certificate revoked and deleted successfully!")
                return True
            else:
                st.error("Failed to delete certificate from Pinata.")
                return False
    except Exception as e:
        st.error(f"Error revoking certificate: {str(e)}")
        return False

def revoke_all_certificates():
    total_certs = len(st.session_state.certificates)
    progress_bar = st.progress(0)
    for i, cert in enumerate(st.session_state.certificates):
        certificate_id = cert['certificate_id']
        revoke_certificate(certificate_id)
        progress_bar.progress((i + 1) / total_certs)
    st.session_state.certificates = []
    save_certificates(st.session_state.certificates)
    st.success("All certificates revoked and deleted successfully!")

def process_bulk_certificates(file, file_type):
    if file is None:
        st.error("Error! Please upload a file!")
        return

    try:
        if file_type == "Excel":
            df = pd.read_excel(file)
        elif file_type == "DOCX":
            df = read_docx(file)
        else:
            st.error("Invalid file! File type is not supported, only supports .docx and .xlsx files")
            return
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return

    if df.empty:
        st.error("The uploaded file is empty. Please upload a valid file with data.")
        return

    df = normalize_column_names(df)
    df = map_columns(df)

    total_rows = len(df)
    if total_rows == 0:
        st.error("No valid data found in the uploaded file after processing.")
        return

    generation_progress_bar = st.progress(0)
    email_progress_bar = st.progress(0)
    generated_count = 0
    email_sent_count = 0
    skipped_details = []

    for index, row in df.iterrows():
        registration_no = row.get('registration_no')
        full_name = row.get('full_name')
        course_name = row.get('course')
        email = row.get('email')

        if not registration_no or not full_name or not course_name or not email:
            skipped_details.append(f"Failed to generate certificate for {registration_no} due to incomplete details")
            continue

        if is_duplicate_registration_no(st.session_state.certificates, registration_no):
            skipped_details.append(f"Failed to generate certificate for {registration_no} due to duplicate registration number")
            continue

        if is_duplicate_email(st.session_state.certificates, email):
            skipped_details.append(f"Failed to generate certificate for {registration_no} due to duplicate email")
            continue

        try:
            candidate_name = full_name.upper()
            institution = st.session_state.selected_institution.split(". ")[1].upper() if ". " in st.session_state.selected_institution else st.session_state.selected_institution.upper()
            registration_no = registration_no.upper()

            safe_filename = f"{registration_no.replace('/', '_').replace('\\', '_')}.pdf"
            pdf_file_path = os.path.join("..", "application", "certificates", safe_filename)
            template_path = os.path.join("..", "assets", "certificate_template.pdf")

            temp_file = "temp_certificate.pdf"

            generate_certificate_pdf({
                'registration_no': registration_no,
                'student_name': candidate_name,
                'course_name': course_name,
                'institution': institution,
                'issue_date': datetime.now().strftime('%Y-%m-%d'),
                'ipfs_hash': ''
            }, temp_file, template_path)

            ipfs_hash = upload_to_pinata(temp_file, api_key, api_secret)
            if ipfs_hash:
                data_to_hash = f"{registration_no}{candidate_name}{course_name}{institution}".encode('utf-8')
                certificate_id = hashlib.sha256(data_to_hash).hexdigest()

                generate_certificate_pdf({
                    'registration_no': registration_no,
                    'student_name': candidate_name,
                    'course_name': course_name,
                    'institution': institution,
                    'issue_date': datetime.now().strftime('%Y-%m-%d'),
                    'ipfs_hash': ipfs_hash
                }, pdf_file_path, template_path)

                tx_receipt = handle_transaction(contract.functions.generateCertificate(
                    certificate_id,
                    registration_no,
                    candidate_name,
                    course_name,
                    institution,
                    ipfs_hash
                ))

                if tx_receipt:
                    st.session_state.certificates.append({
                        "registration_no": registration_no,
                        "email": email,
                        "full_name": candidate_name,
                        "course_name": course_name,
                        "institution": institution,
                        "certificate_id": certificate_id,
                        "ipfsHash": ipfs_hash
                    })
                    save_certificates(st.session_state.certificates)
                    generated_count += 1

                    download_link = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
                    email_status = send_email(email, certificate_id, download_link)
                    if "successfully" in email_status:
                        email_sent_count += 1
                    else:
                        skipped_details.append(f"Failed to generate certificate for {registration_no} due to {email_status}")

            if os.path.exists(temp_file):
                os.remove(temp_file)
            if 'pdf_file_path' in locals() and os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)

        except Exception as e:
            if "Certificate with this ID already exists" in str(e):
                skipped_details.append(f"Failed to generate certificate for {registration_no} due to certificate with this ID already exists")
            else:
                skipped_details.append(f"Failed to generate certificate for {registration_no} due to {str(e)}")
            if 'pdf_file_path' in locals() and os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)

        generation_progress_bar.progress((index + 1) / total_rows, text=f"Generating Certificates: {generated_count}")
        email_progress_bar.progress((index + 1) / total_rows, text=f"Sending Emails: {email_sent_count}")

    st.success(f"{generated_count} certificates successfully generated")
    st.success(f"{email_sent_count} emails successfully sent")
    if skipped_details:
        st.error(f"Skipped {len(skipped_details)} details:")
        for detail in skipped_details:
            st.write(detail)

def refresh_page():
    st.rerun()

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Generate Certificate", "View Certificates", "Manage Institutions", "Revoke Certificate"], key="page")

if page == "Generate Certificate":
    st.header("Generate Certificate")
    if st.button("↻ Refresh", key="refresh_generate"):
        refresh_page()

    # Dropdown menu for selecting institution
    if st.session_state.institutions:
        st.session_state.selected_institution = st.selectbox(
            "Select Institution",
            [inst for inst in st.session_state.institutions], 
            index=0
        )
    else:
        st.session_state.selected_institution = None

    form = st.form("Generate-Certificate")
    Registration_No = form.text_input(label="Registration No").upper()  # Convert to uppercase
    candidate_name = form.text_input(label="Full Name")
    course_name = form.text_input(label="Course Name")
    Institution = st.session_state.selected_institution if st.session_state.selected_institution else form.text_input(label="Institution Name")
    email = form.text_input(label="Student Email")

    submit = form.form_submit_button("Submit")
    if submit:
        if not Registration_No:
            st.error("Registration number cannot be empty!")
        elif not candidate_name:
            st.error("Full name cannot be empty!")
        elif not course_name:
            st.error("Course cannot be empty!")
        elif not Institution:
            st.error("Institution name cannot be empty!")
        elif not email:
            st.error("Email cannot be empty!")
        elif is_duplicate_registration_no(st.session_state.certificates, Registration_No):
            st.error("Registration number already exists!")
        elif is_duplicate_email(st.session_state.certificates, email):
            st.error("Email already used!")
        else:
            try:
                # Convert inputs to uppercase
                candidate_name = candidate_name.upper()
                Institution = Institution.upper()
                Registration_No = Registration_No.upper()
                
                # Create safe filename for local storage
                safe_filename = f"{Registration_No.replace('/', '_').replace('\\', '_')}.pdf"
                pdf_file_path = os.path.join("..", "application", "certificates", safe_filename)
                template_path = os.path.join("..", "assets", "certificate_template.pdf")
                
                # Create temporary file for Pinata
                temp_file = "temp_certificate.pdf"
                
                # Generate certificate without ipfs_hash first
                generate_certificate_pdf({
                    'registration_no': Registration_No,
                    'student_name': candidate_name,
                    'course_name': course_name,
                    'institution': Institution,  # Include institution name
                    'issue_date': datetime.now().strftime('%Y-%m-%d'),
                    'ipfs_hash': ''  # Placeholder for ipfs_hash
                }, temp_file, template_path)

                # Upload to Pinata
                try:
                    ipfs_hash = upload_to_pinata(temp_file, api_key, api_secret)
                    if ipfs_hash:
                        # Generate certificate ID
                        data_to_hash = f"{Registration_No}{candidate_name}{course_name}{Institution}".encode('utf-8')
                        certificate_id = hashlib.sha256(data_to_hash).hexdigest()

                        # Generate certificate with ipfs_hash
                        generate_certificate_pdf({
                            'registration_no': Registration_No,
                            'student_name': candidate_name,
                            'course_name': course_name,
                            'institution': Institution,  # Include institution name
                            'issue_date': datetime.now().strftime('%Y-%m-%d'),
                            'ipfs_hash': ipfs_hash  # Include ipfs_hash
                        }, pdf_file_path, template_path)

                        # Store in blockchain
                        try:
                            tx_receipt = handle_transaction(contract.functions.generateCertificate(
                                certificate_id,
                                Registration_No,
                                candidate_name,
                                course_name,
                                Institution,
                                ipfs_hash
                            ))

                            if tx_receipt:
                                # Log the certificate details
                                print(f"Certificate stored with ID: {certificate_id}")

                                # Save certificate details locally
                                st.session_state.certificates.append({
                                    "registration_no": Registration_No,
                                    "email": email,
                                    "full_name": candidate_name,
                                    "course_name": course_name,
                                    "institution": Institution,
                                    "certificate_id": certificate_id,
                                    "ipfsHash": ipfs_hash
                                })
                                save_certificates(st.session_state.certificates)

                                st.success(f"Certificate successfully generated with ID: {certificate_id}")
                                
                                # Send email to student
                                download_link = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
                                email_status = send_email(email, certificate_id, download_link)
                                st.info(email_status)

                        except Exception as e:
                            st.error(f"Blockchain Error: {str(e)}")
                    else:
                        st.error("Failed to upload the certificate to Pinata. Please try again.")

                finally:
                    # Clean up temporary files
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    if os.path.exists(pdf_file_path):
                        os.remove(pdf_file_path)

            except Exception as e:
                st.error(f"Error generating certificate: {str(e)}")
                if os.path.exists(pdf_file_path):
                    os.remove(pdf_file_path)

    st.header("Bulk Certificate Generation")
    bulk_form = st.form("Bulk-Certificate-Generation")
    bulk_file = bulk_form.file_uploader("Upload Excel or DOCX file", type=["xlsx", "docx"])
    bulk_submit = bulk_form.form_submit_button("Generate Certificates")

    if bulk_submit:
        if bulk_file:
            file_type = "Excel" if bulk_file.name.endswith(".xlsx") else "DOCX"
            process_bulk_certificates(bulk_file, file_type)
        else:
            st.error("Error! Please upload a file!")

elif page == "View Certificates":
    st.header("View Certificates")
    if st.button("↻ Refresh", key="refresh_view"):
        refresh_page()

    form = st.form("View-Certificate")
    certificate_id = form.text_input("Enter the Certificate ID")
    submit = form.form_submit_button("Submit")
    if submit:
        if not certificate_id:
            st.error("Error! Field cannot be empty.")
        else:
            try:
                # Smart Contract Call
                result = contract.functions.isVerified(certificate_id).call()
                if result:
                    st.success("Certificate validated successfully!")
                    view_certificate(certificate_id)
                else:
                    st.error("Invalid Certificate ID! Certificate might be tampered or deleted")
            except Exception as e:
                st.error("Error verifying certificate: Certificate with this ID does not exist.")

elif page == "Manage Institutions":
    st.header("Manage Institutions")
    if st.button("↻ Refresh", key="refresh_manage"):
        refresh_page()

    # Add Institution
    with st.form("Add-Institution"):
        new_institution = st.text_input("New Institution Name")
        add_institution = st.form_submit_button("Add Institution")
        if add_institution and new_institution:
            st.session_state.institutions.append(new_institution)
            save_institutions(st.session_state.institutions)
            st.success(f"Institution '{new_institution}' added successfully!")

    # Display Institutions with Edit and Delete buttons
    if st.session_state.institutions:
        for i, institution in enumerate(st.session_state.institutions):
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                st.write(f"{i+1}. {institution}")
            with col2:
                if st.button("Edit", key=f"edit_{i}"):
                    new_name = st.text_input("New Institution Name", value=institution, key=f"new_name_{i}")
                    if st.button("Save Changes", key=f"save_{i}"):
                        st.session_state.institutions[i] = new_name
                        save_institutions(st.session_state.institutions)
                        st.success(f"Institution renamed to '{new_name}' successfully!")
            with col3:
                if st.button("Delete", key=f"delete_{i}"):
                    st.session_state.institutions.pop(i)
                    save_institutions(st.session_state.institutions)
                    st.success("Institution deleted successfully!")

elif page == "Revoke Certificate":
    st.header("Revoke Certificate")
    if st.button("↻ Refresh", key="refresh_revoke"):
        refresh_page()
    
    # Load certificates from blockchain
    certificates = []
    try:
        for cert in st.session_state.certificates:
            try:
                cert_details = contract.functions.getCertificate(cert['certificate_id']).call()
                if cert_details and cert_details[4]:  # Check if IPFS hash exists
                    certificates.append({
                        'id': cert['certificate_id'],
                        'registration_no': cert_details[0],
                        'candidate_name': cert_details[1],
                        'course_name': cert_details[2],
                        'institution': cert_details[3],
                        'ipfs_hash': cert_details[4],
                        'email': cert['email']  # Add email to the certificate details
                    })
            except Exception:
                continue

        if certificates:
            df = pd.DataFrame(certificates)
            st.dataframe(df)

            cert_id = st.text_input("Enter Certificate ID to revoke")
            if st.button("Revoke Certificate"):
                if cert_id:  # Modified condition to only check cert_id
                    if revoke_certificate(cert_id):
                        time.sleep(2)  # Wait for 2 seconds before refreshing
                        refresh_page()
                    else:
                        st.error("Invalid Certificate ID.")
                else:
                    st.error("Error! Please input Certificate ID. It cannot be empty.")
            
            if st.button("Revoke All Certificates"):
                revoke_all_certificates()
                time.sleep(2)  # Wait for 2 seconds before refreshing
                refresh_page()
        else:
            st.info("No certificates found")
    except Exception as e:
        st.error(f"Error loading certificates: {str(e)}")

# Add logout button at the bottom
logout_placeholder = st.empty()
with logout_placeholder.container():
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.profile = None
        switch_page("app")