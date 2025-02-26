from flask import Flask, render_template, request, jsonify, Response
import boto3
import json
import time
import threading
from botocore.exceptions import ClientError
from get_lambda_logs import get_logs_for_function

app = Flask(__name__)

# Lambda function name to get logs from
LAMBDA_FUNCTION_NAME = "volatileApp"  # Replace with your actual Lambda function name
# Hours of logs to retrieve
LOG_HOURS = 24
# Global variable to store logs
LAMBDA_LOGS = "Logs are being retrieved..."

def refresh_logs():
    """Function to refresh Lambda logs periodically"""
    global LAMBDA_LOGS
    while True:
        try:
            LAMBDA_LOGS = get_logs_for_function(LAMBDA_FUNCTION_NAME, LOG_HOURS)
            print(f"Refreshed logs for Lambda function: {LAMBDA_FUNCTION_NAME}")
        except Exception as e:
            LAMBDA_LOGS = f"Error retrieving Lambda logs: {str(e)}"
            print(LAMBDA_LOGS)
        
        # Sleep for 1 hour before refreshing logs again
        time.sleep(3600)

# Start a background thread to refresh logs periodically
log_thread = threading.Thread(target=refresh_logs, daemon=True)
log_thread.start()

# Initial log retrieval
try:
    LAMBDA_LOGS = get_logs_for_function(LAMBDA_FUNCTION_NAME, LOG_HOURS)
    print(f"Retrieved logs for Lambda function: {LAMBDA_FUNCTION_NAME}")
except Exception as e:
    LAMBDA_LOGS = f"Error retrieving Lambda logs: {str(e)}"
    print(LAMBDA_LOGS)

def retrieve_and_generate_stream(region_name, kb_id, model_arn, query_text):
    """
    Perform a retrieval-augmented generation using the retrieveAndGenerate API
    and stream the response back to the client
    
    Parameters:
    region_name (str): AWS region
    kb_id (str): Knowledge base ID
    model_arn (str): Model ARN (e.g., 'anthropic.claude-v2:1')
    query_text (str): The query text to send
    
    Yields:
    str: Chunks of the model's response for streaming
    """
    try:
        # Initialize Bedrock agent runtime client
        bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=region_name)
        
        # Filter Lambda logs to only include lines with errors
        error_keywords = ['error', 'exception', 'fail', 'traceback', 'warning', 'critical', 'fatal']
        
        # Split logs into lines and filter for error-related content
        log_lines = LAMBDA_LOGS.split('\n')
        error_logs = []
        
        for line in log_lines:
            if any(keyword in line.lower() for keyword in error_keywords):
                error_logs.append(line)
        
        # Join the filtered logs back into a string
        filtered_logs = '\n'.join(error_logs) if error_logs else "No errors found in the logs."
        
        # Include filtered Lambda logs in the query text
        enhanced_query = f"""
Question: {query_text}

Here are the recent error logs from the Lambda function that might be relevant:

{filtered_logs}

Please answer the original question using information from the error logs if relevant. 
If the logs are not relevant to the question, just answer the question directly.
"""
        
        # Prepare the request payload
        request_payload = {
            "input": {
                "text": enhanced_query
            },
            "retrieveAndGenerateConfiguration": {
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": model_arn
                },
                "type": "KNOWLEDGE_BASE"
            }
        }
        
        # Call the retrieveAndGenerate API
        response = bedrock_agent.retrieve_and_generate(
            input=request_payload["input"],
            retrieveAndGenerateConfiguration=request_payload["retrieveAndGenerateConfiguration"]
        )
        
        # Extract the generated text from the response
        generation = response['output']['text']
        
        # Clean up the response
        generation = generation.strip()
        
        # Handle potential "Answer:" prefixes
        if "Answer:" in generation:
            # Split by "Answer:" and take only the first answer
            answers = generation.split("Answer:")
            # The first element might be empty if the response starts with "Answer:"
            for answer in answers:
                if answer.strip():
                    generation = answer.strip()
                    break
            else:
                generation = answers[1].strip()  # Fallback to the first non-empty answer
        
        # Simulate streaming by yielding chunks of the response
        # In a real implementation, you would use a streaming API if available
        words = generation.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= 3 or word.endswith(('.', '!', '?')):
                chunks.append(' '.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Stream each chunk with a small delay to simulate typing
        for chunk in chunks:
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            time.sleep(0.1)  # Simulate typing delay
            
        # Send a completion event
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except ClientError as e:
        error_message = f"Error in retrieve and generate: {e}"
        print(error_message)
        yield f"data: {json.dumps({'error': error_message})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

# Configuration
REGION_NAME = 'us-east-1'
KB_ID = '3JVFPNMRFR'
MODEL_ARN = 'meta.llama3-8b-instruct-v1:0'  # Updated to use ARN format

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/refresh-logs', methods=['POST'])
def refresh_logs_endpoint():
    """Endpoint to manually refresh Lambda logs"""
    global LAMBDA_LOGS
    try:
        LAMBDA_LOGS = get_logs_for_function(LAMBDA_FUNCTION_NAME, LOG_HOURS)
        return jsonify({'status': 'success', 'message': f'Logs for {LAMBDA_FUNCTION_NAME} refreshed successfully'})
    except Exception as e:
        error_message = f"Error retrieving Lambda logs: {str(e)}"
        LAMBDA_LOGS = error_message
        return jsonify({'status': 'error', 'message': error_message}), 500

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        # For SSE streaming (EventSource)
        query = request.args.get('message', '')
    else:
        # For POST requests
        data = request.json
        query = data.get('message', '')
    
    if not query:
        return jsonify({'error': 'No message provided'}), 400
    
    def generate():
        return retrieve_and_generate_stream(REGION_NAME, KB_ID, MODEL_ARN, query)
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
