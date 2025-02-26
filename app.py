from flask import Flask, render_template, request, jsonify
import boto3
import json
from botocore.exceptions import ClientError

app = Flask(__name__)

def retrieve_and_generate(region_name, kb_id, model_id, query_text):
    """
    Perform a retrieval-augmented generation using the knowledge base and Bedrock model
    
    Parameters:
    region_name (str): AWS region
    kb_id (str): Knowledge base ID
    model_id (str): Bedrock model ID (e.g., 'meta.llama3-8b-instruct-v1:0')
    query_text (str): The query text to send
    
    Returns:
    str: The model's response
    """
    try:
        # Initialize Bedrock clients
        bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=region_name)
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # First retrieve relevant information from the knowledge base
        retrieve_response = bedrock_agent.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query_text},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 1
                }
            }
        )
        
        # Extract retrieved passages - limit to top 3 most relevant results
        retrieved_passages = [result['content']['text'] for result in retrieve_response['retrievalResults'][:3]]
        context = "\n\n".join(retrieved_passages)
        
        # Now construct a prompt for the model that encourages a single concise response
        prompt = f"""
        Context information:
        {context}
        
        Question: {query_text}
        
        Provide ONE brief, concise answer to the question based on the context provided.
        Do not repeat yourself or provide multiple answers.
        Keep your response short and to the point, focusing only on the most relevant information.
        Do not prefix your response with "Answer:" or similar labels.
        """
        
        # Call the Bedrock model with the constructed prompt
        # Using lower temperature and max_gen_len to encourage more concise responses
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "prompt": prompt,
                # "temperature": 0.2,  # Even lower temperature for more deterministic responses
                # "top_p": 0.9,
                # "max_gen_len": 150   # Further reduced max length
            })
        )
        
        # Parse the model's response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        generation = response_body['generation']
        
        # Clean up the response - remove any "Answer:" prefixes and extract just the first answer if multiple exist
        if "Answer:" in generation:
            # Split by "Answer:" and take only the first answer
            answers = generation.split("Answer:")
            # The first element might be empty if the response starts with "Answer:"
            for answer in answers:
                if answer.strip():
                    return answer.strip()
            return answers[1].strip()  # Fallback to the first non-empty answer
        
        return generation.strip()
        
    except ClientError as e:
        error_message = f"Error in retrieve and generate: {e}"
        print(error_message)
        return error_message

# Configuration
REGION_NAME = 'us-east-1'
KB_ID = '3JVFPNMRFR'
MODEL_ID = 'meta.llama3-8b-instruct-v1:0'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('message', '')
    
    if not query:
        return jsonify({'error': 'No message provided'}), 400
    
    response = retrieve_and_generate(REGION_NAME, KB_ID, MODEL_ID, query)
    
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
