import json
import streamlit as st
import sys
import os

# Add the project root to path so we can import src modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)



from PIL import Image
import numpy as np
import io
import torch
from huggingface_hub import hf_hub_download
from src.vision.inference import load_model, preprocess_image, run_inference, DEVICE
from src.vision.gradcam_visualization import generate_gradcam, reshape_transform



@st.cache_resource
def load_disease_model():
    try:
        # Download model from Hugging Face Hub
        model_path = hf_hub_download(
            repo_id="bisoye/crop-disease-model",
            filename="model.ckpt"
        )
        
        model = load_model(model_path, DEVICE)
        try:
            st.success("Model loaded from Hugging Face Hub")
        except:
            print("Model loaded from Hugging Face Hub")
        return model
        
    except Exception as e:
        try:
            st.error(f"Error loading model: {e}")
        except:
            print(f"Error loading model: {e}")
        return None


def process_image_for_analysis(uploaded_file):
    """Process uploaded image for AI analysis"""
        
    try:
        # Convert uploaded file to PIL Image
        image = Image.open(uploaded_file).convert("RGB")
        
        # Save original image bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        original_image_bytes = img_byte_arr.getvalue()
        
        # Apply the same transforms as in your inference.py
        try:
            import albumentations as A
            from albumentations.pytorch import ToTensorV2
        except ImportError:
            st.error("albumentations not installed. Please run: pip install albumentations")
            return None, None, None
        
        image_array = np.array(image.resize((224, 224)))
        
        MEAN = [0.485, 0.456, 0.406]
        STD = [0.229, 0.224, 0.225]
        
        transforms = A.Compose([
            A.Resize(224, 224),
            A.Normalize(mean=MEAN, std=STD),
            ToTensorV2()
        ])
        
        transformed = transforms(image=image_array)
        input_tensor = transformed["image"].unsqueeze(0)
        
        return image, original_image_bytes, input_tensor
        
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None, None, None

def analyze_crop_image(image, input_tensor, model):
    """Analyze crop image and generate results"""
        
    try:
        # Run inference
        predicted_class, confidence, label = run_inference(model, input_tensor, DEVICE)
        
        # Generate GradCAM
        # You may need to adjust target_layer based on your model architecture
        gradcam_viz = generate_gradcam(
            image=image, 
            input_tensor=input_tensor, 
            model=model,
            reshape_transform=reshape_transform if hasattr(model.model, 'layers') else None
        )
        
        # Convert GradCAM to bytes
        gradcam_image = Image.fromarray(gradcam_viz)
        gradcam_byte_arr = io.BytesIO()
        gradcam_image.save(gradcam_byte_arr, format='PNG')
        gradcam_image_bytes = gradcam_byte_arr.getvalue()
        
        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'label': label,
            'gradcam_image_bytes': gradcam_image_bytes,
            'gradcam_image': gradcam_image
        }
        
    except Exception as e:
        st.error(f"Error during analysis: {e}")
        st.error(f"Model type: {type(model)}")
        st.error(f"Input tensor shape: {input_tensor.shape}")
        return None

def format_disease_name(label: str) -> str:
    """Format disease label for display"""
    # Remove underscores and capitalize
    formatted = label.replace('_', ' ').title()
    
    # Handle specific formatting
    if '__' in label:
        parts = label.split('__')
        crop = parts[0].replace('_', ' ').title()
        condition = parts[1].replace('_', ' ').title()
        return f"{crop}: {condition}"
    
    return formatted

def load_disease_info():
    """Load disease information from JSON file"""
    info_path = r'diseases.json'
    
    with open(info_path, 'r') as f:
        disease_info = json.load(f)
    return disease_info['plant_diseases']


def get_disease_info(label: str) -> dict:
    return load_disease_info().get(label, {})