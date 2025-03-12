import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_email(to_email, subject, body):
    # Load environment variables
    load_dotenv()
    
    # Get the institution name from session state
    institution_name = st.session_state.get("selected_institution", "Your Institution")
    
    # Get the email credentials from environment variables
    from_email = os.getenv("institute_email")
    password = os.getenv("institute_password")
    
    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = f"{institution_name} <{from_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    # Send the email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")
