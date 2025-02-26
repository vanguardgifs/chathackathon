# ProdPal Web Chat

ProdPal is an AI assistant for answering questions about products and services, powered by AWS Bedrock and retrieval-augmented generation (RAG).

## Features

- Web-based chat interface similar to ChatGPT or Claude
- Retrieval-augmented generation using AWS Bedrock
- Concise, accurate answers based on your knowledge base
- Responsive design that works on desktop and mobile

## Setup

1. Run the setup script to configure AWS credentials and install dependencies:

```
setup_env.bat
```

This script will:
- Check if AWS credentials exist, and if not, prompt you to enter them
- Set up a Python virtual environment
- Install required packages

2. Start the web server:

```
python app.py
```

3. Open your browser and navigate to:

```
http://localhost:5000
```

## Configuration

The application uses the following AWS resources:

- Region: us-east-1 (default)
- Knowledge Base ID: 3JVFPNMRFR
- Model ID: meta.llama3-8b-instruct-v1:0

You can modify these settings in the `app.py` file if needed.

## Requirements

- Python 3.8 or higher
- AWS account with access to Bedrock
- AWS credentials with appropriate permissions

## Files

- `app.py` - Flask web server and API endpoints
- `templates/index.html` - HTML template for the chat interface
- `static/css/style.css` - CSS styles for the chat interface
- `static/js/script.js` - JavaScript for handling chat functionality
- `setup_env.bat` - Setup script for AWS credentials and dependencies
- `requirements.txt` - Python package dependencies
