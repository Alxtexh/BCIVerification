import streamlit as st
import fitz  # PyMuPDF
from pyzbar.pyzbar import decode
from PIL import Image
from utils.streamlit_utils import displayPDF, hide_icons, hide_sidebar, remove_whitespaces, view_certificate
from connection import contract
import os  # Import the os module
import hashlib  # Import hashlib for certificate ID verification
import json  # Import json for QR code data parsing
from streamlit_extras.switch_page_button import switch_page  # Import switch_page for navigation

st.set_page_config(
    page_title="Verifier",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)
hide_icons()
hide_sidebar()
remove_whitespaces()

options = ("Verify Certificate using PDF", "View/Verify Certificate using Certificate ID")
selected = st.selectbox("", options, label_visibility="hidden")

def extract_qr_code_from_pdf(pdf_path):
    try:
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            # Get a higher resolution image for better QR code reading
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Increased resolution
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Try to decode QR code
            decoded_objects = decode(img)
            for obj in decoded_objects:
                if obj.type == "QRCODE":
                    # Clean up the decoded data
                    qr_data = json.loads(obj.data.decode("utf-8").strip())
                    return qr_data
        return None
    except Exception as e:
        st.error(f"Error extracting QR code from PDF: {e}")
        return None

def verify_certificate(qr_data):
    try:
        # Log the certificate ID being verified
        certificate_id = qr_data["certificate_id"]
        print(f"Verifying Certificate ID: {certificate_id}")

        # Check if the certificate ID exists
        if not contract.functions.certificateExists(certificate_id).call():
            return False, "Certificate with this ID does not exist"

        # Get the certificate details from the blockchain
        certificate_details = contract.functions.getCertificate(certificate_id).call()

        # Verify all details match
        if (certificate_details[0] == qr_data["registration_no"] and
            certificate_details[1] == qr_data["student_name"] and
            certificate_details[2] == qr_data["course_name"] and
            certificate_details[3] == qr_data["institution"]):
            return True, certificate_details
        else:
            # Log the mismatched details
            print(f"Mismatch Details: Registration No: {certificate_details[0]} != {qr_data['registration_no']}, "
                  f"Full Name: {certificate_details[1]} != {qr_data['student_name']}, "
                  f"Course Name: {certificate_details[2]} != {qr_data['course_name']}, "
                  f"Institution: {certificate_details[3]} != {qr_data['institution']}")
            return False, "Certificate details mismatch"
    except Exception as e:
        return False, str(e)

if selected == options[0]:
    uploaded_file = st.file_uploader("Upload the PDF version of the certificate")
    if uploaded_file is not None:
        # Save the uploaded file
        with open("temp_certificate.pdf", "wb") as file:
            file.write(uploaded_file.getvalue())
        
        try:
            # Extract and decode the QR code
            qr_data = extract_qr_code_from_pdf("temp_certificate.pdf")
            
            if qr_data:
                is_valid, result = verify_certificate(qr_data)
                
                if is_valid:
                    st.success("✅ Certificate Verified Successfully! Kindly check if all the details match this in the system..")
                    view_certificate(qr_data["certificate_id"])
                else:
                    st.error(f"❌ Certificate verification failed: {result}")
            else:
                st.error("❌ No valid QR code found in the certificate!")
        except Exception as e:
            st.error(f"❌ Error processing certificate: {str(e)}")
        finally:
            # Ensure temporary file is removed
            if os.path.exists("temp_certificate.pdf"):
                os.remove("temp_certificate.pdf")

elif selected == options[1]:
    form = st.form("Validate-Certificate")
    certificate_id = form.text_input("Enter the Certificate ID")
    submit = form.form_submit_button("Validate")
    if submit:
        if not certificate_id:
            st.error("Error! Field cannot be empty.")
        else:
            try:
                result = contract.functions.isVerified(certificate_id).call()
                if result:
                    st.success("Certificate validated successfully!")
                    view_certificate(certificate_id)
                else:
                    st.error("Invalid Certificate ID! Certificate might be tampered or deleted")
            except Exception as e:
                st.error("Error verifying certificate: Certificate with this ID does not exist.")

# Add a "Go Back" button to redirect to the home page
if st.button("Go Back"):
    switch_page("app")
