import hashlib
import streamlit as st
from datetime import datetime
from typing import Optional, Tuple, List, Dict
import os
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()

# Initialize Supabase client
try:
    from supabase import create_client, Client
    
    # Check for environment variables first (local .env), then Streamlit secrets (cloud)
    supabase_url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_ANON_KEY", "")
    
    if supabase_url and supabase_key:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Connected to Supabase")
    else:
        raise Exception("Supabase credentials not found")
        
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    supabase = None

def init_database():
    """Initialize the database with users and analyses tables"""
    if supabase is None:
        print("Error: Supabase connection not available")
        return
        
    # Note: Run these commands in your Supabase SQL editor if tables don't exist:
    print("""
    If tables don't exist, run these in your Supabase SQL editor:
    
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
        created_at TIMESTAMP DEFAULT NOW(),
        disease_info JSONB NOT NULL 
    );
    """)

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, email: str, name: str, password: str) -> bool:
    """Create a new user in the database"""
    if supabase is None:
        try:
            st.error("Database connection not available")
        except:
            print("Database connection not available")
        return False
        
    try:
        password_hash = hash_password(password)
        
        result = supabase.table('users').insert({
            'username': username,
            'email': email,
            'name': name,
            'password_hash': password_hash
        }).execute()
        
        return len(result.data) > 0
        
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            return False
        try:
            st.error(f"Database error: {e}")
        except:
            print(f"Database error: {e}")
        return False

def verify_user(username: str, password: str) -> Optional[Tuple[str, str, int]]:
    """Verify user credentials and return (name, email, user_id) if valid"""
    if supabase is None:
        return None
        
    try:
        password_hash = hash_password(password)
        
        result = supabase.table('users').select('name, email, id').eq('username', username).eq('password_hash', password_hash).execute()
        
        if result.data:
            user = result.data[0]
            return (user['name'], user['email'], user['id'])
        return None
        
    except Exception as e:
        try:
            st.error(f"Database error: {e}")
        except:
            print(f"Database error: {e}")
        return None

def username_exists(username: str) -> bool:
    """Check if username already exists"""
    if supabase is None:
        return False
        
    try:
        result = supabase.table('users').select('id').eq('username', username).execute()
        return len(result.data) > 0
    except Exception:
        return False

def email_exists(email: str) -> bool:
    """Check if email already exists"""
    if supabase is None:
        return False
        
    try:
        result = supabase.table('users').select('id').eq('email', email).execute()
        return len(result.data) > 0
    except Exception:
        return False

def save_analysis(user_id: int, original_image_bytes: bytes, gradcam_image_bytes: bytes, 
                 predicted_class: int, confidence: float, label: str, disease_info: dict) -> bool:
    """Save crop disease analysis to database"""
    if supabase is None:
        try:
            st.error("Database connection not available")
        except:
            print("Database connection not available")
        return False
        
    try:
        import base64
        
        # Convert bytes to base64 for storage
        original_image_b64 = base64.b64encode(original_image_bytes).decode('utf-8')
        gradcam_image_b64 = base64.b64encode(gradcam_image_bytes).decode('utf-8')
        
        result = supabase.table('analyses').insert({
            'user_id': user_id,
            'original_image': original_image_b64,
            'gradcam_image': gradcam_image_b64,
            'predicted_class': str(predicted_class),
            'confidence': confidence,
            'label': label,
            'disease_info': disease_info
        }).execute()
        
        return len(result.data) > 0
        
    except Exception as e:
        try:
            st.error(f"Error saving analysis: {e}")
        except:
            print(f"Error saving analysis: {e}")
        return False

def get_user_analyses(user_id: int, limit: int = 50) -> List[Dict]:
    """Get user's analysis history"""
    if supabase is None:
        return []
        
    try:
        import base64
        
        result = supabase.table('analyses').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        
        analyses = []
        for row in result.data:
            # Convert base64 back to bytes
            try:
                original_image = base64.b64decode(row['original_image'].encode('utf-8'))
                gradcam_image = base64.b64decode(row['gradcam_image'].encode('utf-8'))
            except:
                continue
                
            analyses.append({
                'id': row['id'],
                'original_image': original_image,
                'gradcam_image': gradcam_image,
                'predicted_class': row['predicted_class'],
                'confidence': row['confidence'],
                'label': row['label'],
                'created_at': row['created_at'],
                'disease_info': row['disease_info']
            })
        
        return analyses
        
    except Exception as e:
        try:
            st.error(f"Error retrieving analyses: {e}")
        except:
            print(f"Error retrieving analyses: {e}")
        return []

def get_analysis_stats(user_id: int) -> Dict:
    """Get user's analysis statistics"""
    if supabase is None:
        return {'total_analyses': 0, 'last_analysis': None, 'top_diseases': []}
        
    try:
        # Total analyses
        total_result = supabase.table('analyses').select('id', count='exact').eq('user_id', user_id).execute()
        total_analyses = total_result.count or 0
        
        # Most recent analysis
        recent_result = supabase.table('analyses').select('created_at').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
        last_analysis = recent_result.data[0]['created_at'] if recent_result.data else None
        
        # Top predicted diseases - get all analyses and process in Python
        all_analyses = supabase.table('analyses').select('label').eq('user_id', user_id).execute()
        
        # Count diseases manually
        disease_counts = {}
        for analysis in all_analyses.data:
            label = analysis['label']
            disease_counts[label] = disease_counts.get(label, 0) + 1
        
        # Sort by count and take top 5
        top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_analyses': total_analyses,
            'last_analysis': last_analysis,
            'top_diseases': top_diseases
        }
        
    except Exception as e:
        try:
            st.error(f"Error getting stats: {e}")
        except:
            print(f"Error getting stats: {e}")
        return {'total_analyses': 0, 'last_analysis': None, 'top_diseases': []}



# import sqlite3
# import hashlib
# import streamlit as st
# import base64
# from datetime import datetime
# from typing import Optional, Tuple, List, Dict

# DB_PATH = "users.db"

# def init_database():
#     """Initialize the database with users and analyses tables"""
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
    
#     # Users table
#     c.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             email TEXT UNIQUE NOT NULL,
#             name TEXT NOT NULL,
#             password_hash TEXT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     """)
    
#     # Analyses table for storing crop disease predictions
#     c.execute("""
#         CREATE TABLE IF NOT EXISTS analyses (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             original_image BLOB NOT NULL,
#             gradcam_image BLOB,
#             predicted_class TEXT NOT NULL,
#             confidence REAL NOT NULL,
#             label TEXT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (user_id) REFERENCES users (id)
#         )
#     """)
    
#     conn.commit()
#     conn.close()

# def hash_password(password: str) -> str:
#     """Hash password using SHA-256"""
#     return hashlib.sha256(password.encode()).hexdigest()

# def create_user(username: str, email: str, name: str, password: str) -> bool:
#     """Create a new user in the database"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         password_hash = hash_password(password)
        
#         c.execute("""
#             INSERT INTO users (username, email, name, password_hash)
#             VALUES (?, ?, ?, ?)
#         """, (username, email, name, password_hash))
        
#         conn.commit()
#         conn.close()
#         return True
        
#     except sqlite3.IntegrityError:
#         return False
#     except Exception as e:
#         st.error(f"Database error: {e}")
#         return False

# def verify_user(username: str, password: str) -> Optional[Tuple[str, str, int]]:
#     """Verify user credentials and return (name, email, user_id) if valid"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         password_hash = hash_password(password)
        
#         c.execute("""
#             SELECT name, email, id FROM users 
#             WHERE username = ? AND password_hash = ?
#         """, (username, password_hash))
        
#         result = c.fetchone()
#         conn.close()
        
#         return result if result else None
        
#     except Exception as e:
#         st.error(f"Database error: {e}")
#         return None

# def username_exists(username: str) -> bool:
#     """Check if username already exists"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
#         result = c.fetchone()
#         conn.close()
        
#         return result is not None
        
#     except Exception:
#         return False

# def email_exists(email: str) -> bool:
#     """Check if email already exists"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         c.execute("SELECT 1 FROM users WHERE email = ?", (email,))
#         result = c.fetchone()
#         conn.close()
        
#         return result is not None
        
#     except Exception:
#         return False

# def save_analysis(user_id: int, original_image_bytes: bytes, gradcam_image_bytes: bytes, 
#                  predicted_class: int, confidence: float, label: str) -> bool:
#     """Save crop disease analysis to database"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         c.execute("""
#             INSERT INTO analyses (user_id, original_image, gradcam_image, predicted_class, confidence, label)
#             VALUES (?, ?, ?, ?, ?, ?)
#         """, (user_id, original_image_bytes, gradcam_image_bytes, predicted_class, confidence, label))
        
#         conn.commit()
#         conn.close()
#         return True
        
#     except Exception as e:
#         st.error(f"Error saving analysis: {e}")
#         return False

# def get_user_analyses(user_id: int, limit: int = 50) -> List[Dict]:
#     """Get user's analysis history"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         c.execute("""
#             SELECT id, original_image, gradcam_image, predicted_class, confidence, label, created_at
#             FROM analyses 
#             WHERE user_id = ?
#             ORDER BY created_at DESC
#             LIMIT ?
#         """, (user_id, limit))
        
#         results = c.fetchall()
#         conn.close()
        
#         analyses = []
#         for row in results:
#             analyses.append({
#                 'id': row[0],
#                 'original_image': row[1],
#                 'gradcam_image': row[2],
#                 'predicted_class': row[3],
#                 'confidence': row[4],
#                 'label': row[5],
#                 'created_at': row[6]
#             })
        
#         return analyses
        
#     except Exception as e:
#         st.error(f"Error retrieving analyses: {e}")
#         return []

# def get_analysis_stats(user_id: int) -> Dict:
#     """Get user's analysis statistics"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
        
#         # Total analyses
#         c.execute("SELECT COUNT(*) FROM analyses WHERE user_id = ?", (user_id,))
#         total_analyses = c.fetchone()[0]
        
#         # Most recent analysis
#         c.execute("""
#             SELECT created_at FROM analyses 
#             WHERE user_id = ? 
#             ORDER BY created_at DESC 
#             LIMIT 1
#         """, (user_id,))
#         recent_result = c.fetchone()
#         last_analysis = recent_result[0] if recent_result else None
        
#         # Top predicted diseases
#         c.execute("""
#             SELECT label, COUNT(*) as count 
#             FROM analyses 
#             WHERE user_id = ? 
#             GROUP BY label 
#             ORDER BY count DESC 
#             LIMIT 5
#         """, (user_id,))
#         top_diseases = c.fetchall()
        
#         conn.close()
        
#         return {
#             'total_analyses': total_analyses,
#             'last_analysis': last_analysis,
#             'top_diseases': top_diseases
#         }
        
#     except Exception as e:
#         st.error(f"Error getting stats: {e}")
#         return {'total_analyses': 0, 'last_analysis': None, 'top_diseases': []}