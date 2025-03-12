import streamlit as st
from PIL import Image
from utils.streamlit_utils import hide_icons, hide_sidebar, remove_whitespaces
from streamlit_extras.switch_page_button import switch_page
from web3 import Web3

if __name__ == '__main__':
    st.set_page_config(
        page_title="BCV Application",
        page_icon="🎓",  
        layout="wide"
    )

# Initialize Web3 connection
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))  # adjust URL if needed

hide_icons()
hide_sidebar()
remove_whitespaces()

# Custom CSS to make the title move and hide the sidebar
moving_title_css = '''
<style>
@keyframes move {
    0% { transform: translateX(0); }
    50% { transform: translateX(20px); }
    100% { transform: translateX(0); }
}

.moving-title {
    display: inline-block;
    animation: move 2s infinite;
}

.css-1d391kg {  /* Hide the sidebar */
    display: none;
}
</style>
'''

st.markdown(moving_title_css, unsafe_allow_html=True)
st.markdown('<h1 class="moving-title">Certificate Verification System With Blockchain</h1>', unsafe_allow_html=True)

st.subheader("Select Your Role")

col1, col2 = st.columns(2)
institite_logo = Image.open("../assets/institute_logo.jpg")
with col1:
    st.image(institite_logo, output_format="jpg", width=150)
    clicked_institute = st.button("Institute")

company_logo = Image.open("../assets/company_logo.jpg")
with col2:
    st.image(company_logo, output_format="jpg", width=150)
    clicked_verifier = st.button("Verifier")

if clicked_institute:
    st.session_state.profile = "Institute"
    switch_page('login')
elif clicked_verifier:
    st.session_state.profile = "Verifier"
    switch_page('verifier')

# About Project section
st.markdown("## About Project")
st.markdown("""
By leveraging technology to store certificates on a platform the information becomes both immutable and transparent.

This integration of capabilities with the verification process paves the way for an efficient and reliable system to manage and validate certificates across domains, like education, employment, professional certifications and more.
""")

# Copyright notice
st.markdown("<p style='text-align: center;'>© 2025 AlxTexh</p>", unsafe_allow_html=True)
