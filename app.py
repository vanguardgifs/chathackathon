from flask import Flask, render_template, request, jsonify
import boto3
import json
from botocore.exceptions import ClientError

app = Flask(__name__)

def retrieve_and_generate(region_name, kb_id, model_arn, query_text):
    """
    Perform a retrieval-augmented generation using the retrieveAndGenerate API
    
    Parameters:
    region_name (str): AWS region
    kb_id (str): Knowledge base ID
    model_arn (str): Model ARN (e.g., 'anthropic.claude-v2:1')
    query_text (str): The query text to send
    
    Returns:
    str: The model's response
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
                    return answer.strip()
            return answers[1].strip()  # Fallback to the first non-empty answer
        
        return generation
        
    except ClientError as e:
        error_message = f"Error in retrieve and generate: {e}"
        print(error_message)
        return error_message

# Configuration
REGION_NAME = 'us-east-1'
KB_ID = '3JVFPNMRFR'
MODEL_ARN = 'meta.llama3-8b-instruct-v1:0'  # Updated to use ARN format

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('message', '')
    
    if not query:
        return jsonify({'error': 'No message provided'}), 400
    
    response = retrieve_and_generate(REGION_NAME, KB_ID, MODEL_ARN, query)
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
