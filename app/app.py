import streamlit as st
from database import init_database

# Initialize database on app start
init_database()

# Page config
st.set_page_config(
    page_title="Authentication App",
    page_icon="🏠",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
.main-container {
    text-align: center;
    padding: 3rem 2rem;
}
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 3rem 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
}
.feature-card {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Hero section
st.markdown("""
<div class="hero-section">
    <h1>🏠 Welcome to AgriAI</h1>
</div>
""", unsafe_allow_html=True)

# Check if user is already logged in
if st.session_state.get('logged_in', False):
    st.success(f"✅ Welcome back, {st.session_state.get('name', 'User')}!")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📊 Go to Dashboard", use_container_width=True):
            st.switch_page("pages/dashboard.py")
else:
    # Main navigation
    st.markdown("### 🚀 Get Started")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🔑 Sign In</h3>
            <p>Already have an account? Welcome back!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔑 Sign In", use_container_width=True):
            st.switch_page("pages/login.py")
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Sign Up</h3>
            <p>New here? Create your account today!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📝 Sign Up", use_container_width=True):
            st.switch_page("pages/signup.py")

