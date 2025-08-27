# AgriAI - Crop Disease Detection System

A web-based application that uses machine learning to identify crop diseases from images and provides treatment recommendations to farmers.

## Features

- **AI-Powered Disease Detection**: Upload crop images for automated disease classification across 88+ categories
- **Visual Explanations**: GradCAM visualizations show which areas of the image the AI focused on for diagnosis  
- **Comprehensive Disease Database**: Detailed information including causes, symptoms, and treatment recommendations
- **User Authentication**: Secure account system for tracking analysis history
- **Analysis Dashboard**: View previous diagnoses, statistics, and filter results
- **Camera Integration**: Take photos directly within the app or upload from device
- **Cloud Database**: All user data and analyses stored securely in the cloud

## Supported Crops & Diseases

The model can identify diseases across multiple crops including:

- **Fruits**: Apple, Cherry, Grape, Mango, Peach, Strawberry
- **Vegetables**: Tomato, Potato, Pepper, Cucumber, Chili
- **Staple Crops**: Rice, Corn, Wheat, Soybean
- **Cash Crops**: Coffee, Tea, Sugarcane, Cotton, Cassava

Total of 88 disease categories including healthy classifications.

## Technology Stack

### Frontend
- **Streamlit**: Web application framework
- **Python**: Core programming language

### Machine Learning
- **PyTorch Lightning**: Model training framework
- **TIMM**: Pre-trained vision models
- **Albumentations**: Image preprocessing and augmentation
- **GradCAM**: Model interpretability and visualization

### Backend
- **Supabase**: PostgreSQL database and authentication
- **Hugging Face Hub**: Model hosting and distribution

### Deployment
- **Streamlit Cloud**: Application hosting
- **Environment Management**: python-dotenv for local development

## Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AgriAI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment variables**
   Create a `.env` file in the project root:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   ```

4. **Initialize database**
   Run these SQL commands in your Supabase SQL editor:
   ```sql
   -- Users table
   CREATE TABLE IF NOT EXISTS users (
       id SERIAL PRIMARY KEY,
       username VARCHAR(50) UNIQUE NOT NULL,
       email VARCHAR(100) UNIQUE NOT NULL,
       name VARCHAR(100) NOT NULL,
       password_hash VARCHAR(64) NOT NULL,
       created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Analyses table
   CREATE TABLE IF NOT EXISTS analyses (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       original_image TEXT NOT NULL,
       gradcam_image TEXT NOT NULL,
       predicted_class VARCHAR(10) NOT NULL,
       confidence REAL NOT NULL,
       label VARCHAR(100) NOT NULL,
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Production Deployment

1. **Deploy to Streamlit Cloud**
   - Connect your GitHub repository to Streamlit Cloud
   - Add environment variables in the app settings:
     - `SUPABASE_URL`
     - `SUPABASE_ANON_KEY`

2. **Model hosting** is handled automatically via Hugging Face Hub

## Project Structure

```
AgriAI/
├── app.py                 # Main application entry point
├── database.py           # Database operations and user management
├── ai_utils.py          # AI model utilities and image processing
├── diseases.json        # Disease information database
├── requirements.txt     # Python dependencies
├── .env                 # Local environment variables (not committed)
├── pages/
│   ├── login.py        # User authentication
│   ├── signup.py       # User registration
│   ├── crop_analysis.py # Main disease detection interface
│   └── dashboard.py    # User dashboard and analysis history
└── src/
    └── vision/
        ├── inference.py           # Model inference utilities
        ├── gradcam_visualization.py # GradCAM implementation
        └── lit_model.py          # PyTorch Lightning model definition
```

## Usage

1. **Create Account**: Register with email, username, and password
2. **Login**: Access your personal dashboard
3. **Upload Image**: Take a photo or upload an image of the affected crop
4. **Get Analysis**: AI provides disease classification and confidence score
5. **View Results**: See GradCAM visualization and treatment recommendations
6. **Track History**: All analyses are saved to your personal dashboard

## Model Information

- **Architecture**: Vision Transformer (ViT) and CNN-based models
- **Training**: PyTorch Lightning framework
- **Classes**: 88 crop disease categories
- **Input**: 224x224 RGB images
- **Preprocessing**: Resize, normalize, and tensor conversion

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: User email address
- `name`: Full name
- `password_hash`: SHA-256 hashed password
- `created_at`: Account creation timestamp

### Analyses Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `original_image`: Base64 encoded original image
- `gradcam_image`: Base64 encoded GradCAM visualization
- `predicted_class`: Numeric class prediction
- `confidence`: Prediction confidence score (0-1)
- `label`: Human-readable disease name
- `created_at`: Analysis timestamp

## Security Considerations

- **Password Security**: SHA-256 hashing for user passwords
- **Data Isolation**: User data separated by user_id foreign keys
- **Environment Variables**: Sensitive credentials stored in environment variables
- **Cloud Database**: Production data stored securely in Supabase

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Dependencies

### Core Requirements
- `streamlit>=1.28.0`
- `supabase>=2.0.0`
- `python-dotenv>=1.0.0`

### Machine Learning
- `torch>=2.0.0`
- `torchvision>=0.15.0`
- `pytorch-lightning>=2.0.0`
- `timm>=0.9.0`
- `albumentations>=1.3.0`
- `pytorch-grad-cam>=1.4.0`

### Image Processing
- `pillow>=10.0.0`
- `numpy>=1.24.0`
- `opencv-python>=4.8.0`

### Model Distribution
- `huggingface_hub>=0.16.0`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Disease information compiled from agricultural research sources
- Model training data from various crop disease datasets
- Built with Streamlit for rapid web application development
- Powered by Supabase for reliable cloud database services
