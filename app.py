from flask import Flask, render_template, request, jsonify, Response
import boto3
import json
import time
from botocore.exceptions import ClientError

app = Flask(__name__)

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
        
        # Prepare the request payload
        request_payload = {
            "input": {
                "text": query_text
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
