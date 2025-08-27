import streamlit as st
from database import init_database, verify_user

# Initialize database
init_database()

# Page config
st.set_page_config(
    page_title="Login",
    page_icon="🔑",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
<style>
.login-container {
    max-width: 400px;
    margin: 0 auto;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🔑 Welcome Back!")
st.markdown("---")

# Login form
with st.form("login_form"):
    st.subheader("Sign In to Your Account")
    
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    submitted = st.form_submit_button("🚀 Sign In", use_container_width=True)
    
    if submitted:
        if not username or not password:
            st.error("❌ Please fill in all fields")
        else:
            user_data = verify_user(username, password)
            
            if user_data:
                name, email, user_id = user_data
                
                # Set session state
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['name'] = name
                st.session_state['email'] = email
                st.session_state['user_id'] = user_id
                
                st.success(f"✅ Welcome back, {name}!")
                st.balloons()
                
                # Redirect to dashboard
                st.switch_page("pages/dashboard.py")
                
            else:
                st.error("❌ Invalid username or password")

# Divider
st.markdown("---")

# Sign up link
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("### Don't have an account?")
    if st.button("📝 Create Account", use_container_width=True):
        st.switch_page("pages/signup.py")

# Footer
st.markdown("---")
st.caption("🔐 Secure login system")