import streamlit as st
from db.firebase_app import register  # Import the register function from firebase_app module
from streamlit_extras.switch_page_button import switch_page  # Import the switch_page function for navigation
from utils.streamlit_utils import hide_icons, hide_sidebar, remove_whitespaces  # Import utility functions

# Set the page configuration
st.set_page_config(
    page_title="Register",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide icons, sidebar, and remove whitespaces using utility functions
hide_icons()
hide_sidebar()
remove_whitespaces()

# Create a form for login/registration
form = st.form("login")
email = form.text_input("Enter your email")  # Input field for email
password = form.text_input("Enter your password", type="password")  # Input field for password
clicked_login = st.button("Already registered? Click here to login!")  # Button to switch to login page

# Handle the login button click
if clicked_login:
    if st.session_state.profile == "Institute":
        switch_page("institute_login")  # Redirect to institute login page if profile is "Institute"
    else:
        switch_page("verifier_login")  # Redirect to verifier login page otherwise

# Handle the registration form submission
submit = form.form_submit_button("Register")
if submit:
    if not email:
        st.error("Email cannot be empty!")
    elif not password:
        st.error("Password cannot be empty!")
    else:
        result = register(email, password)  # Call the register function with email and password
        if result == "success":
            st.success("Registration successful!")  # Show success message if registration is successful
            if st.session_state.profile == "Institute":
                switch_page("institute")  # Redirect to institute page if profile is "Institute"
            else:
                switch_page("verifier")  # Redirect to verifier page otherwise
        else:
            st.error("Registration unsuccessful! User exists!!")  # Show error message if registration fails