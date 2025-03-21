# ProdPal Web Chat

ProdPal is an AI assistant for answering questions about products and services, powered by AWS Bedrock and retrieval-augmented generation (RAG).

## Features

- Web-based chat interface similar to ChatGPT or Claude
- Retrieval-augmented generation using AWS Bedrock
- Streaming responses that appear gradually as they're generated
- Lambda logs integration for troubleshooting and monitoring
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
- Model ARN: anthropic.claude-v2:1

You can modify these settings in the `app.py` file if needed.

## API Implementation

The application uses AWS Bedrock's retrieveAndGenerate API, which combines retrieval and generation in a single API call. This approach:

1. Retrieves relevant information from your knowledge base based on the user's query
2. Automatically generates a concise response using the specified model
3. Returns a single, focused answer without repetition

### Streaming Implementation

The application implements streaming responses using Server-Sent Events (SSE):

1. The backend simulates streaming by breaking the response into chunks
2. These chunks are sent to the frontend as they become available
3. The frontend progressively displays the chunks, creating a typing effect
4. This provides a more engaging user experience similar to ChatGPT and Claude

### Lambda Logs Integration

The application integrates with AWS Lambda logs to provide insights into your serverless functions:

1. Logs are automatically retrieved on startup and refreshed hourly
2. A "Refresh Logs" button allows manual refresh of the latest logs
3. **Only error-related log lines** are included in the context for every query
4. The application filters logs for keywords like 'error', 'exception', 'fail', etc.
5. This focuses the context on relevant issues while reducing noise
6. **Responses include numbered citations** that show sources on hover
7. Citations appear as [1], [2], etc. with full source details on hover
8. Users can ask about errors without explicitly mentioning "logs" in their query
9. Configure the Lambda function name in `app.py` by setting the `LAMBDA_FUNCTION_NAME` variable

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
