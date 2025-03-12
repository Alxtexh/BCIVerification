import streamlit as st
from db.firebase_app import login
from dotenv import load_dotenv
import os
from streamlit_extras.switch_page_button import switch_page
from utils.streamlit_utils import hide_icons, hide_sidebar, remove_whitespaces

# Set the page configuration with a wide layout and collapsed sidebar
st.set_page_config(
    page_title="Login",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit's default icons
hide_icons()

# Hide the sidebar
hide_sidebar()

# Remove extra whitespaces from the page
remove_whitespaces()

# Load environment variables from a .env file
load_dotenv()

# Create a form for login
form = st.form("login")

# Add a text input field for the email
email = form.text_input("Enter your email")

# Add a password input field
password = form.text_input("Enter your password", type="password")

# Check if the user's profile is not "Institute"
if st.session_state.profile != "Institute":
    # Add a button for new user registration
    clicked_register = st.button("New user? Click here to register!")

    # If the register button is clicked, switch to the register page
    if clicked_register:
        switch_page("register")

# Add a submit button to the form
submit = form.form_submit_button("Login")

# If the form is submitted
if submit:
    if not email:
        st.error("Email cannot be empty!")
    elif not password:
        st.error("Password cannot be empty!")
    else:
        # If the user's profile is "Institute"
        if st.session_state.profile == "Institute":
            # Get the valid email and password from environment variables
            valid_email = os.getenv("institute_email")
            valid_pass = os.getenv("institute_password")
            
            # Check if the entered email and password match the valid credentials
            if email == valid_email and password == valid_pass:
                st.session_state.logged_in = True  # Set logged_in to True
                switch_page("institute")
            else:
                st.error("Invalid credentials!")
        else:
            # Handle other profiles if needed
            pass
