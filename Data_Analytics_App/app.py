from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
import logging
from werkzeug.utils import secure_filename
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import sqlite3
from contextlib import closing
import openai
import json
import numpy as np

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx'}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'analytics.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # For session management

# OpenAI Configuration - USE YOUR OWN KEY HERE
app.config['OPENAI_API_KEY'] = ''  # Replace with your actual API key
app.config['DEFAULT_MODEL'] = 'gpt-3.5-turbo'

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database with correct schema
def init_db():
    with closing(sqlite3.connect(app.config['DATABASE'])) as conn:
        # Drop existing table if it has the wrong schema
        conn.execute("DROP TABLE IF EXISTS analyses")
        
        # Create new table with correct schema
        conn.execute('''CREATE TABLE IF NOT EXISTS analyses
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT NOT NULL,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      user_ip TEXT,
                      row_count INTEGER,
                      column_count INTEGER)''')
        conn.commit()

init_db()

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_visualizations(df):
    try:
        visuals = {}
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            plt.figure(figsize=(8, 4))
            df[col].hist()
            plt.title(f'Distribution of {col}')
            plt.tight_layout()
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            visuals[f'{col}_hist'] = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close()
        return visuals
    except Exception as e:
        logger.error(f"Visualization failed: {str(e)}")
        return {}

def generate_ai_insights(df, model=None):
    """Generate AI insights using OpenAI API with the app's configured key"""
    if not app.config['OPENAI_API_KEY']:
        return {"error": "No OpenAI API key configured", "insights": None}
    
    try:
        # Set the API key from app config
        openai.api_key = app.config['OPENAI_API_KEY']
        
        # Use the specified model or default
        model_to_use = model or app.config['DEFAULT_MODEL']
        
        # Create a text summary of the data for the prompt
        sample_data = df.head(3).to_string()
        numeric_summary = df.describe().to_string() if len(df.select_dtypes(include=['number']).columns) > 0 else "No numeric columns"
        
        prompt = f"""Analyze this dataset and provide concise insights:
        1. Identify 3-5 key characteristics of the data
        2. Note any obvious data quality issues
        3. Suggest potential analysis directions
        
        Data sample (first 3 rows):
        {sample_data}
        
        Numeric summary:
        {numeric_summary}
        
        Dataset shape: {len(df.columns)} columns, {len(df)} rows
        
        Provide the response in bullet points with clear headings."""
        
        response = openai.ChatCompletion.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": "You are a helpful data analyst. Provide clear, concise insights about datasets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return {
            "success": True,
            "insights": response.choices[0].message.content,
            "model": model_to_use,
            "usage": response.usage
        }
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return {"error": str(e), "insights": None}

def get_clean_summary(df):
    """Generate a clean, simplified summary of the dataframe"""
    summary = {
        "file_info": {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "numeric_columns": list(df.select_dtypes(include=['number']).columns)
        },
        "numeric_summary": {}
    }
    
    numeric_cols = df.select_dtypes(include=['number'])
    if not numeric_cols.empty:
        summary_stats = numeric_cols.describe().transpose()
        summary_stats = summary_stats[['mean', 'min', '50%', 'max']]
        summary_stats.columns = ['Average', 'Minimum', 'Median', 'Maximum']
        
        # Convert NaN values to None for JSON serialization
        numeric_summary_dict = summary_stats.to_dict('index')
        for col in numeric_summary_dict:
            for stat in numeric_summary_dict[col]:
                if pd.isna(numeric_summary_dict[col][stat]):
                    numeric_summary_dict[col][stat] = None
        
        summary["numeric_summary"] = numeric_summary_dict
    
    return summary

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "details": str(e)}), 400

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "File too large", "details": "Maximum file size is 5MB"}), 413

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Upload endpoint
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({"error": "Invalid file type. Only CSV and Excel files are allowed."}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file temporarily
        file.save(filepath)
        
        try:
            # Read the file based on extension
            if filename.lower().endswith('.csv'):
                try:
                    df = pd.read_csv(filepath)
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(filepath, encoding='latin1')
                    except Exception as e:
                        logger.error(f"CSV read error: {str(e)}")
                        return jsonify({"error": "Could not read CSV file. Please check the file encoding."}), 400
            else:  # Excel
                try:
                    df = pd.read_excel(filepath)
                except Exception as e:
                    logger.error(f"Excel read error: {str(e)}")
                    return jsonify({"error": "Could not read Excel file. Please check the file format."}), 400
            
            # Remove temporary file
            try:
                os.remove(filepath)
            except:
                pass
            
            # Store analysis record with correct columns
            with closing(sqlite3.connect(app.config['DATABASE'])) as conn:
                conn.execute('''INSERT INTO analyses 
                              (filename, user_ip, row_count, column_count) 
                              VALUES (?, ?, ?, ?)''',
                            [filename, request.remote_addr, len(df), len(df.columns)])
                conn.commit()
            
            # Generate results
            summary = get_clean_summary(df)
            visualizations = generate_visualizations(df)
            
            # Always generate AI insights using the app's API key
            model = request.form.get('model', app.config['DEFAULT_MODEL'])
            ai_insights = generate_ai_insights(df, model)
            
            response_data = {
                "success": True,
                "filename": filename,
                "summary": summary,
                "visualizations": visualizations,
                "ai_insights": ai_insights
            }
            
            return jsonify(response_data)
            
        except pd.errors.EmptyDataError:
            logger.error("Empty file uploaded")
            return jsonify({"error": "The file is empty."}), 400
        except pd.errors.ParserError:
            logger.error("Invalid file format")
            return jsonify({"error": "Invalid file format."}), 400
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return jsonify({"error": "An error occurred while processing the file.", "details": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

# Frontend
@app.route('/')
def serve_index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)