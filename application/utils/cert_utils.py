import qrcode
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
import os
import hashlib
import json

def generate_certificate_pdf(certificate_data, file_path, template_path):
    # Ensure file_path is not empty
    if not file_path:
        raise ValueError("The file_path parameter is empty")

    # Register custom fonts
    pdfmetrics.registerFont(TTFont('Damion', '../assets/Damion.ttf'))
    pdfmetrics.registerFont(TTFont('Playball', '../assets/Playball.ttf'))

    # Generate the certificate ID consistently
    data_to_hash = f"{certificate_data['registration_no']}{certificate_data['student_name']}{certificate_data['course_name']}{certificate_data['institution']}".encode('utf-8')
    certificate_id = hashlib.sha256(data_to_hash).hexdigest()

    # Log the generated certificate ID
    print(f"Generated Certificate ID: {certificate_id}")

    # Generate QR code with all the certificate details
    qr_data = {
        "certificate_id": certificate_id,
        "registration_no": certificate_data['registration_no'],
        "student_name": certificate_data['student_name'],
        "course_name": certificate_data['course_name'],
        "institution": certificate_data['institution']
    }

    # Log the QR code data
    print(f"QR Code Data: {qr_data}")

    qr_data_json = json.dumps(qr_data)  # Serialize to JSON
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=2
    )
    qr.add_data(qr_data_json)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR code as an image
    qr_code_path = os.path.join("..", "assets", "qr_code.png")
    img.save(qr_code_path)

    # Create the directory if it does not exist
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    # Create a temporary PDF with the user inputs
    temp_folder = os.path.join("..", "application", "temp")
    os.makedirs(temp_folder, exist_ok=True)
    temp_pdf_path = os.path.join(temp_folder, "temp_certificate.pdf")
    c = canvas.Canvas(temp_pdf_path, pagesize=landscape(letter))
    
    # Add the certificate details
    c.setFont("Damion", 36)
    c.drawString(3*inch, 5*inch, certificate_data['student_name'])
    
    c.setFont("Playball", 18)
    c.drawString(3*inch, 4.5*inch, f"Registration Number: {certificate_data['registration_no']}")
    c.drawString(3*inch, 4*inch, f"Course: {certificate_data['course_name']}")
    c.drawString(3*inch, 3.5*inch, f"Institution: {certificate_data['institution']}")  # Add institution name

    # Draw the QR code at the bottom left
    c.drawImage(qr_code_path, 0.5 * inch, 0.5 * inch, 1.5 * inch, 1.5 * inch)

    # Add issue date at the bottom right in white color with larger font size
    c.setFont("Playball", 12)  # Increase font size
    c.setFillColorRGB(1, 1, 1)  # Set text color to white
    c.drawString(9.9 * inch, 0.5 * inch, certificate_data['issue_date'])  # Adjust position

    # Save the temporary PDF
    c.save()

    # Read the template PDF and the temporary PDF
    with open(template_path, "rb") as template_file, open(temp_pdf_path, "rb") as temp_file:
        template_pdf = PdfReader(template_file)
        temp_pdf = PdfReader(temp_file)

        # Create a new PDF with the template and the new content
        output = PdfWriter()
        page = template_pdf.pages[0]
        page.merge_page(temp_pdf.pages[0])
        output.add_page(page)

        # Save the new PDF
        with open(file_path, "wb") as outputStream:
            output.write(outputStream)

    # Clean up the temporary PDF and QR code image
    os.remove(temp_pdf_path)
    os.remove(qr_code_path)

