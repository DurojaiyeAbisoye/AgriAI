import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import save_analysis
from ai_utils import load_disease_model, process_image_for_analysis, analyze_crop_image, format_disease_name, get_disease_info

# Check authentication
if not st.session_state.get('logged_in', False):
    st.error("🚫 Please log in to access this page")
    if st.button("🔑 Go to Login"):
        st.switch_page("pages/login.py")
    st.stop()

# Page config
st.set_page_config(
    page_title="Crop Disease Analysis",
    page_icon="🌱",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.analysis-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
}
.result-card {
    background: rgba(40, 167, 69, 0.1);
    border: 2px solid rgba(40, 167, 69, 0.3);
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
}
.warning-card {
    background: rgba(255, 193, 7, 0.1);
    border: 2px solid rgba(255, 193, 7, 0.3);
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
}
.error-card {
    background: rgba(220, 53, 69, 0.1);
    border: 2px solid rgba(220, 53, 69, 0.3);
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
}
.result-card h3, .warning-card h3, .error-card h3 {
    margin-top: 0;
    color: var(--text-color);
}
.result-card p, .warning-card p, .error-card p {
    margin-bottom: 0;
    color: var(--text-color);
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="analysis-container">
    <h1>🌱 Crop Disease Analysis</h1>
    <p>Upload an image of your crop to detect diseases and get treatment recommendations</p>
</div>
""", unsafe_allow_html=True)

# Load model
with st.spinner("🔄 Loading AI model..."):
    model = load_disease_model()

if model is None:
    st.error("❌ Could not load the AI model. Please check the model path configuration.")
    st.info("💡 Make sure to update the MODEL_CHECKPOINT_PATH in ai_utils.py")
    st.stop()

st.success("✅ AI model loaded successfully!")

# Sidebar with user info and navigation
with st.sidebar:
    st.header(f"👤 {st.session_state.get('name', 'User')}")
    st.write(f"**Username:** {st.session_state.get('username', 'N/A')}")
    
    st.markdown("---")
    
    # Navigation
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")
    
    if st.button("📊 View My Analyses", use_container_width=True):
        st.switch_page("pages/dashboard.py")
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("pages/login.py")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📸 Upload Crop Image")
    
    # Image upload options
    upload_option = st.radio(
        "Choose how to provide your image:",
        ["📁 Upload from device", "📷 Take photo with camera"]
    )
    
    uploaded_file = None
    
    if upload_option == "📁 Upload from device":
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of the crop leaf or plant"
        )
    else:
        uploaded_file = st.camera_input("Take a photo of your crop")
    
    if uploaded_file is not None:
        # Clear previous results when new image is uploaded
        if 'current_analysis' in st.session_state:
            del st.session_state['current_analysis']
        
        # Display uploaded image
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        
        # Analysis button
        if st.button("🔬 Analyze Image", type="primary", use_container_width=True):
            with st.spinner("🤖 Analyzing your crop image..."):
                # Process image
                image, original_image_bytes, input_tensor = process_image_for_analysis(uploaded_file)
                
                if image is not None and input_tensor is not None:
                    # Run AI analysis
                    results = analyze_crop_image(image, input_tensor, model)
                    
                    if results:
                        # Save to database
                        user_id = st.session_state.get('user_id')
                        analysis_saved = save_analysis(
                            user_id=user_id,
                            original_image_bytes=original_image_bytes,
                            gradcam_image_bytes=results['gradcam_image_bytes'],
                            predicted_class=results['predicted_class'],
                            confidence=results['confidence'],
                            label=results['label'],
                            disease_info=get_disease_info(results['label']),
                        )
                        
                        if analysis_saved:
                            st.session_state['current_analysis'] = results
                            st.session_state['current_analysis']['original_image'] = image
                            st.success("✅ Analysis completed and saved!")
                        else:
                            st.error("❌ Failed to save analysis to database")
                    else:
                        st.error("❌ Analysis failed. Please try again.")
                else:
                    st.error("❌ Failed to process image. Please try again.")

with col2:
    st.subheader("📋 Analysis Results")
    
    # Display results if available
    if 'current_analysis' in st.session_state:
        results = st.session_state['current_analysis']
        
        # Format disease name
        formatted_label = format_disease_name(results['label'])
        confidence_pct = results['confidence'] * 100
        
        # Determine result type
        is_healthy = 'healthy' in results['label'].lower()
        is_high_confidence = results['confidence'] > 0.8
        
        if is_healthy and is_high_confidence:
            card_class = "result-card"
            icon = "✅"
        elif is_high_confidence:
            card_class = "error-card"
            icon = "⚠️"
        else:
            card_class = "warning-card"
            icon = "❓"
        
        st.markdown(f"""
        <div class="{card_class}">
            <h3>{icon} {formatted_label}</h3>
            <p><strong>Confidence:</strong> {confidence_pct:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show GradCAM visualization
        st.subheader("🎯 AI Attention Map (GradCAM)")
        st.image(results['gradcam_image'], caption="Areas the AI focused on for diagnosis", use_container_width=True)
        st.caption("Red areas show where the AI detected important features for the diagnosis")
        
        # Disease information
        disease_info = get_disease_info(results['label'])
        with st.expander("📖 Disease Information", expanded=True):
            
            st.write(f"**Cause:** {disease_info['cause']}")
            # Symptoms section
            st.write("**Symptoms:**")
            for i, symptom in enumerate(disease_info['symptoms'], 1):
                st.write(f"{i}. {symptom}")
            
            # Treatment section
            st.write("**Treatment & Management:**")
            for i, treatment in enumerate(disease_info['treatment'], 1):
                st.write(f"{i}. {treatment}")
            
            # Additional advice for healthy crops
            if 'healthy' in results['label'].lower():
                st.success("✅ **Good News:** Your crop appears healthy! Continue with regular care and monitoring.")
        
        # Clear results button
        if st.button("🗑️ Clear Results"):
            if 'current_analysis' in st.session_state:
                del st.session_state['current_analysis']
            st.rerun()
    else:
        st.info("👆 Upload an image and click 'Analyze' to see results here")

# Instructions section
st.markdown("---")
st.subheader("📋 How to Use")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 1. 📸 Capture Image
    - Upload a clear image of the affected crop
    - Ensure good lighting and focus
    - Include the diseased area in the frame
    """)

with col2:
    st.markdown("""
    #### 2. 🔬 AI Analysis
    - Click 'Analyze Image' to start
    - AI will detect diseases and highlight focus areas
    - Get confidence scores and disease information
    """)

with col3:
    st.markdown("""
    #### 3. 📊 Track History
    - All analyses are automatically saved
    - View your analysis history in the dashboard
    - Monitor crop health over time
    """)

# Footer
st.markdown("---")
st.caption(f"🕒 Current session: {st.session_state.get('name', 'User')} | 🤖 AI-powered crop disease detection")