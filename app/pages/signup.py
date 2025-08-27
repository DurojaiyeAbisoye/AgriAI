import streamlit as st
import re
from database import init_database, create_user, username_exists, email_exists, verify_user

# Initialize database
init_database()

# Page config
st.set_page_config(
    page_title="Sign Up",
    page_icon="📝",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
.signup-container {
    max-width: 400px;
    margin: 0 auto;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Valid password"

# Title
st.title("📝 Create Your Account")
st.markdown("---")

# Signup form
with st.form("signup_form"):
    st.subheader("Join Us Today!")
    
    name = st.text_input("Full Name", placeholder="Enter your full name")
    email = st.text_input("Email", placeholder="Enter your email address")
    username = st.text_input("Username", placeholder="Choose a username")
    password = st.text_input("Password", type="password", placeholder="Create a secure password")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
    
    # Terms checkbox
    terms_accepted = st.checkbox("I agree to the Terms of Service and Privacy Policy")
    
    submitted = st.form_submit_button("🎉 Create Account", use_container_width=True)
    
    if submitted:
        # Validation
        errors = []
        
        if not name or len(name.strip()) < 2:
            errors.append("Name must be at least 2 characters long")
            
        if not email or not validate_email(email):
            errors.append("Please enter a valid email address")
            
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long")
            
        if not password:
            errors.append("Password is required")
        else:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors.append(msg)
                
        if password != confirm_password:
            errors.append("Passwords do not match")
            
        if not terms_accepted:
            errors.append("You must accept the Terms of Service")
            
        # Check if username/email already exist
        if not errors:
            if username_exists(username):
                errors.append("Username already taken")
                
            if email_exists(email):
                errors.append("Email already registered")
        
        # Display errors or create account
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Create the user
            if create_user(username, email, name.strip(), password):
                st.success("✅ Account created successfully!")
                st.balloons()
                
                # Get the user_id for auto-login
                user_data = verify_user(username, password)
                if user_data:
                    user_name, user_email, user_id = user_data
                    
                    # Auto-login the user
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['name'] = name.strip()
                    st.session_state['email'] = email
                    st.session_state['user_id'] = user_id
                
                st.info("🚀 Redirecting to dashboard...")
                st.switch_page("pages/dashboard.py")
            else:
                st.error("❌ Failed to create account. Please try again.")

# Divider
st.markdown("---")

# Login link
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("### Already have an account?")
    if st.button("🔑 Sign In", use_container_width=True):
        st.switch_page("pages/login.py")

# Footer
st.markdown("---")
st.caption("🔐 Your data is safe with us")