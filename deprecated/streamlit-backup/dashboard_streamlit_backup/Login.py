import streamlit as st
from utils.log_api_client import LogApiClient
import time

st.set_page_config(
    page_title="Login",
    page_icon="👋",
)

st.title("Welcome to the Trading Dashboard 👋")
st.write("Please log in to continue.")

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- Login Logic ---
def login(username, password):
    """Attempts to log in the user via the API."""
    try:
        client = LogApiClient()
        token_data = client.login(username, password)
        if token_data and "access_token" in token_data:
            st.session_state['authenticated'] = True
            st.session_state['token'] = token_data['access_token']
            st.session_state['username'] = username
            return True
    except Exception as e:
        st.error(f"Login failed: {e}")
        return False
    return False

# --- Logout Logic ---
def logout():
    """Logs out the user."""
    st.session_state['authenticated'] = False
    st.session_state['token'] = None
    st.session_state['username'] = ""
    st.success("You have been logged out.")
    time.sleep(1) # Brief pause to show the message
    st.experimental_rerun()

# --- Page Rendering ---
if st.session_state['authenticated']:
    st.success(f"Logged in as **{st.session_state['username']}**.")
    st.write("You can now access the other pages via the sidebar.")
    st.button("Logout", on_click=logout)
else:
    with st.form("login_form"):
        username = st.text_input("Username", value="testuser")
        password = st.text_input("Password", type="password", value="testpass")
        submitted = st.form_submit_button("Login")

        if submitted:
            if login(username, password):
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

# --- Sidebar Management ---
# This part is a bit of a trick for Streamlit. 
# We are essentially hiding the other pages if not logged in.
if not st.session_state['authenticated']:
    st.stop() 