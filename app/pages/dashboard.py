import streamlit as st
import sys
import os
from datetime import datetime
import base64
from PIL import Image
import io

# Add parent directory to path for database imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_user_analyses, get_analysis_stats
from ai_utils import format_disease_name

# Check if user is authenticated
if not st.session_state.get('logged_in', False):
    st.error("🚫 Access Denied: Please log in to view this page")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔑 Go to Login", use_container_width=True):
            st.switch_page("pages/login.py")
    
    st.stop()

# Page config
st.set_page_config(
    page_title="My Crop Analyses",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.dashboard-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 2rem;
}
.wip-container {
    text-align: center;
    padding: 4rem 2rem;
    background-color: #f8f9fa;
    border-radius: 15px;
    border: 2px dashed #dee2e6;
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="dashboard-header">
    <h1>📊 My Crop Analyses</h1>
    <p>View your analysis history and track crop health over time</p>
</div>
""", unsafe_allow_html=True)

# Get user data
user_id = st.session_state.get('user_id')
user_name = st.session_state.get('name', 'User')

# Load user statistics
stats = get_analysis_stats(user_id)

# User info sidebar
with st.sidebar:
    st.header("👤 User Profile")
    
    # Display user info
    st.info(f"""
    **Name:** {st.session_state.get('name', 'N/A')}  
    **Username:** {st.session_state.get('username', 'N/A')}  
    **Email:** {st.session_state.get('email', 'N/A')}
    """)
    
    st.markdown("---")
    
    # Navigation
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")
    
    if st.button("🌱 New Analysis", use_container_width=True):
        st.switch_page("pages/crop_analysis.py")
    
    st.markdown("---")
    
    # Logout button
    if st.button("🚪 Logout", use_container_width=True):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.success("👋 Logged out successfully!")
        st.switch_page("pages/login.py")

# Statistics Overview
st.subheader("📈 Your Analysis Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📊 Total Analyses",
        value=stats['total_analyses'],
        delta=None
    )

with col2:
    last_analysis = stats['last_analysis']
    if last_analysis:
        # Parse the datetime and format it
        try:
            last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
            formatted_date = last_date.strftime("%m/%d/%Y")
        except:
            formatted_date = "Recently"
    else:
        formatted_date = "Never"
    
    st.metric(
        label="🕐 Last Analysis",
        value=formatted_date,
        delta=None
    )

with col3:
    healthy_count = sum(1 for disease, count in stats['top_diseases'] if 'healthy' in disease.lower())
    diseased_count = stats['total_analyses'] - healthy_count
    
    st.metric(
        label="🌿 Healthy Crops",
        value=healthy_count,
        delta=f"+{healthy_count - diseased_count}" if healthy_count > diseased_count else None
    )

with col4:
    st.metric(
        label="⚠️ Issues Detected",
        value=diseased_count,
        delta=f"+{diseased_count}" if diseased_count > 0 else None
    )

# Top diseases section
if stats['top_diseases']:
    st.subheader("🔍 Most Common Issues Detected")
    
    disease_col1, disease_col2 = st.columns([2, 1])
    
    with disease_col1:
        for disease, count in stats['top_diseases'][:5]:
            formatted_disease = format_disease_name(disease)
            progress_value = count / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
            st.progress(progress_value, text=f"{formatted_disease}: {count} times")
    
    with disease_col2:
        st.write("**Detection Summary:**")
        for disease, count in stats['top_diseases'][:3]:
            percentage = (count / stats['total_analyses']) * 100 if stats['total_analyses'] > 0 else 0
            st.write(f"• {count} analyses ({percentage:.1f}%)")

# Analysis History
st.subheader("📋 Recent Analyses")

# Load user analyses
analyses = get_user_analyses(user_id, limit=20)
if analyses:
    # Filters
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        show_healthy = st.checkbox("Show Healthy", value=True)
    with col2:
        show_diseased = st.checkbox("Show Diseased", value=True)
    with col3:
        confidence_filter = st.slider("Minimum Confidence", 0.0, 1.0, 0.0, 0.1)
    
    # Filter analyses
    filtered_analyses = []
    for analysis in analyses:
        is_healthy = 'healthy' in analysis['label'].lower()
        meets_confidence = analysis['confidence'] >= confidence_filter
        
        if meets_confidence and ((is_healthy and show_healthy) or (not is_healthy and show_diseased)):
            filtered_analyses.append(analysis)
    
    if filtered_analyses:
        for i, analysis in enumerate(filtered_analyses):
            with st.expander(f"Analysis {i+1}: {format_disease_name(analysis['label'])} ({analysis['confidence']*100:.1f}% confidence)", expanded=False):
                
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                
                with col1:
                    st.write("**Original Image:**")
                    try:
                        original_img = Image.open(io.BytesIO(analysis['original_image']))
                        st.image(original_img, use_container_width=True)
                    except Exception as e:
                        st.error("Could not load original image")
                
                with col2:
                    st.write("**GradCAM Visualization:**")
                    try:
                        gradcam_img = Image.open(io.BytesIO(analysis['gradcam_image']))
                        st.image(gradcam_img, use_container_width=True)
                    except Exception as e:
                        st.error("Could not load GradCAM image")
                
                with col3:
                    st.write("**Analysis Details:**")
                    st.write(f"**Disease:** {format_disease_name(analysis['label'])}")
                    st.write(f"**Confidence:** {analysis['confidence']*100:.1f}%")
                    
                    # Format date
                    try:
                        date_obj = datetime.fromisoformat(analysis['created_at'].replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
                    except:
                        formatted_date = analysis['created_at']
                    
                    st.write(f"**Date:** {formatted_date}")
                    
                    # Status indicator
                    if 'healthy' in analysis['label'].lower():
                        st.success("✅ Healthy")
                    else:
                        st.warning("⚠️ Disease Detected")
                with col4:
                    st.write("**Disease Information:**")
                    disease_info = analysis.get('disease_info', {})
                    if disease_info:
                        st.write(f"**Cause:** {disease_info.get('cause', 'N/A')}")
                        st.write("**Symptoms:**")
                        symptoms = disease_info.get('symptoms', [])
                        if symptoms:
                            for symptom in symptoms:
                                st.write(f"- {symptom}")
                        else:
                            st.write("N/A")
                        st.write(f"**Management:** {disease_info.get('management', 'N/A')}")
                    else:
                        st.write("No additional information available.")
    else:
        st.info("No analyses match your current filters.")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🌱 Analyze A Crop", use_container_width=True, type="primary"):
            st.switch_page("pages/crop_analysis.py")
else:
    # No analyses yet
    st.info("📋 No previous analyses found. Start by analyzing your first crop image!")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🌱 Analyze Your First Crop", use_container_width=True, type="primary"):
            st.switch_page("pages/crop_analysis.py")

# Footer
st.markdown("---")
st.caption(f"🕒 Last updated: Just now | 👤 Logged in as: {st.session_state.get('name', 'User')}")

# import streamlit as st
# import sys
# import os
# from datetime import datetime
# import base64
# from PIL import Image
# import io

# # Add parent directory to path for database imports
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from database import get_user_analyses, get_analysis_stats
# from ai_utils import format_disease_name

# # Check if user is authenticated
# if not st.session_state.get('logged_in', False):
#     st.error("🚫 Access Denied: Please log in to view this page")
    
#     col1, col2, col3 = st.columns([1, 1, 1])
#     with col2:
#         if st.button("🔑 Go to Login", use_container_width=True):
#             st.switch_page("pages/login.py")
    
#     st.stop()

# # Page config
# st.set_page_config(
#     page_title="My Crop Analyses",
#     page_icon="📊",
#     layout="wide"
# )

# # Custom CSS
# st.markdown("""
# <style>
# .dashboard-header {
#     background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
#     padding: 2rem;
#     border-radius: 10px;
#     color: white;
#     margin-bottom: 2rem;
# }
# .wip-container {
#     text-align: center;
#     padding: 4rem 2rem;
#     background-color: #f8f9fa;
#     border-radius: 15px;
#     border: 2px dashed #dee2e6;
#     margin: 2rem 0;
# }
# </style>
# """, unsafe_allow_html=True)

# # Header
# st.markdown("""
# <div class="dashboard-header">
#     <h1>📊 My Crop Analyses</h1>
#     <p>View your analysis history and track crop health over time</p>
# </div>
# """, unsafe_allow_html=True)

# # Get user data
# user_id = st.session_state.get('user_id')
# user_name = st.session_state.get('name', 'User')

# # Load user statistics
# stats = get_analysis_stats(user_id)

# # User info sidebar
# with st.sidebar:
#     st.header("👤 User Profile")
    
#     # Display user info
#     st.info(f"""
#     **Name:** {st.session_state.get('name', 'N/A')}  
#     **Username:** {st.session_state.get('username', 'N/A')}  
#     **Email:** {st.session_state.get('email', 'N/A')}
#     """)
    
#     st.markdown("---")
    
#     # Navigation
#     if st.button("🏠 Home", use_container_width=True):
#         st.switch_page("app.py")
    
#     if st.button("🌱 New Analysis", use_container_width=True):
#         st.switch_page("pages/crop_analysis.py")
    
#     st.markdown("---")
    
#     # Logout button
#     if st.button("🚪 Logout", use_container_width=True):
#         # Clear all session state
#         for key in list(st.session_state.keys()):
#             del st.session_state[key]
        
#         st.success("👋 Logged out successfully!")
#         st.switch_page("pages/login.py")

# # Statistics Overview
# st.subheader("📈 Your Analysis Overview")

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     st.metric(
#         label="📊 Total Analyses",
#         value=stats['total_analyses'],
#         delta=None
#     )

# with col2:
#     last_analysis = stats['last_analysis']
#     if last_analysis:
#         # Parse the datetime and format it
#         try:
#             last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
#             formatted_date = last_date.strftime("%m/%d/%Y")
#         except:
#             formatted_date = "Recently"
#     else:
#         formatted_date = "Never"
    
#     st.metric(
#         label="🕐 Last Analysis",
#         value=formatted_date,
#         delta=None
#     )

# with col3:
#     healthy_count = sum(1 for disease, count in stats['top_diseases'] if 'healthy' in disease.lower())
#     diseased_count = stats['total_analyses'] - healthy_count
    
#     st.metric(
#         label="🌿 Healthy Crops",
#         value=healthy_count,
#         delta=f"+{healthy_count - diseased_count}" if healthy_count > diseased_count else None
#     )

# with col4:
#     st.metric(
#         label="⚠️ Issues Detected",
#         value=diseased_count,
#         delta=f"+{diseased_count}" if diseased_count > 0 else None
#     )

# # Top diseases section
# if stats['top_diseases']:
#     st.subheader("🔍 Most Common Issues Detected")
    
#     disease_col1, disease_col2 = st.columns([2, 1])
    
#     with disease_col1:
#         for disease, count in stats['top_diseases'][:5]:
#             formatted_disease = format_disease_name(disease)
#             progress_value = count / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
#             st.progress(progress_value, text=f"{formatted_disease}: {count} times")
    
#     with disease_col2:
#         st.write("**Detection Summary:**")
#         for disease, count in stats['top_diseases'][:3]:
#             percentage = (count / stats['total_analyses']) * 100 if stats['total_analyses'] > 0 else 0
#             st.write(f"• {count} analyses ({percentage:.1f}%)")

# # Analysis History
# st.subheader("📋 Recent Analyses")

# # Load user analyses
# analyses = get_user_analyses(user_id, limit=20)

# if analyses:
#     # Filters
#     col1, col2, col3 = st.columns([1, 1, 2])
    
#     with col1:
#         show_healthy = st.checkbox("Show Healthy", value=True)
#     with col2:
#         show_diseased = st.checkbox("Show Diseased", value=True)
#     with col3:
#         confidence_filter = st.slider("Minimum Confidence", 0.0, 1.0, 0.0, 0.1)
    
#     # Filter analyses
#     filtered_analyses = []
#     for analysis in analyses:
#         is_healthy = 'healthy' in analysis['label'].lower()
#         meets_confidence = analysis['confidence'] >= confidence_filter
        
#         if meets_confidence and ((is_healthy and show_healthy) or (not is_healthy and show_diseased)):
#             filtered_analyses.append(analysis)
    
#     if filtered_analyses:
#         for i, analysis in enumerate(filtered_analyses):
#             with st.expander(f"Analysis {i+1}: {format_disease_name(analysis['label'])} ({analysis['confidence']*100:.1f}% confidence)", expanded=False):
                
#                 col1, col2, col3 = st.columns([1, 1, 1])
                
#                 with col1:
#                     st.write("**Original Image:**")
#                     try:
#                         original_img = Image.open(io.BytesIO(analysis['original_image']))
#                         st.image(original_img, use_container_width=True)
#                     except Exception as e:
#                         st.error("Could not load original image")
                
#                 with col2:
#                     st.write("**GradCAM Visualization:**")
#                     try:
#                         gradcam_img = Image.open(io.BytesIO(analysis['gradcam_image']))
#                         st.image(gradcam_img, use_container_width=True)
#                     except Exception as e:
#                         st.error("Could not load GradCAM image")
                
#                 with col3:
#                     st.write("**Analysis Details:**")
#                     st.write(f"**Disease:** {format_disease_name(analysis['label'])}")
#                     st.write(f"**Confidence:** {analysis['confidence']*100:.1f}%")
                    
#                     # Format date
#                     try:
#                         date_obj = datetime.fromisoformat(analysis['created_at'].replace('Z', '+00:00'))
#                         formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
#                     except:
#                         formatted_date = analysis['created_at']
                    
#                     st.write(f"**Date:** {formatted_date}")
                    
#                     # Status indicator
#                     if 'healthy' in analysis['label'].lower():
#                         st.success("✅ Healthy")
#                     else:
#                         st.warning("⚠️ Disease Detected")
#     else:
#         st.info("No analyses match your current filters.")

# else:
#     # No analyses yet
#     st.info("📋 No previous analyses found. Start by analyzing your first crop image!")
    
#     col1, col2, col3 = st.columns([1, 1, 1])
#     with col2:
#         if st.button("🌱 Analyze Your First Crop", use_container_width=True, type="primary"):
#             st.switch_page("pages/crop_analysis.py")


# if st.button("🌱 Analyze A Crop", use_container_width=True, type="primary"):
#             st.switch_page("pages/crop_analysis.py")

# # Footer
# st.markdown("---")
# st.caption(f"🕒 Last updated: Just now | 👤 Logged in as: {st.session_state.get('name', 'User')}")