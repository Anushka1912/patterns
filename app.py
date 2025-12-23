from flask import Flask, request, jsonify
from pathlib import Path
import tempfile
import os
from formats import extract_invoice_data

app = Flask(__name__)

# Configure max file size (16 MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/extract', methods=['POST'])
def extract_invoice():
    """
    Extract invoice data from uploaded text file.
    Expects a file upload with key 'file' in the request.
    Returns JSON with extracted invoice data.
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload a file with key "file"'
            }), 400
        
        file = request.files['file']
        
        # Check if file has a filename
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Check file extension
        if not file.filename.endswith('.txt'):
            return jsonify({
                'error': 'Invalid file type',
                'message': 'Only .txt files are allowed'
            }), 400
        
        # Read file content
        try:
            text_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({
                'error': 'File encoding error',
                'message': 'File must be UTF-8 encoded text'
            }), 400
        
        # Extract invoice data
        extracted_data = extract_invoice_data(text_content)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'data': extracted_data
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Extraction failed',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Invoice extraction API is running'
    }), 200

@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'Invoice Data Extraction API',
        'version': '1.0',
        'endpoints': {
            'POST /extract': {
                'description': 'Extract invoice data from text file',
                'parameters': {
                    'file': 'Text file (multipart/form-data)'
                },
                'response': 'JSON with extracted invoice data'
            },
            'GET /health': {
                'description': 'Health check endpoint'
            }
        },
        'example': {
            'curl': 'curl -X POST -F "file=@invoice.txt" http://localhost:5000/extract'
        }
    }), 200

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({
        'error': 'File too large',
        'message': 'File size exceeds 16 MB limit'
    }), 413

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)