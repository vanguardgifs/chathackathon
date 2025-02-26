import boto3
print(f"Running boto3 version: {boto3.__version__}")

from botocore.exceptions import ClientError
from get_lambda_logs import get_logs_for_function

import json

from flask import Flask, request, Response

app = Flask(__name__)

def retrieve_and_generate(region_name, kb_id, model_id, query_text, prompt=None, lambda_function=None, hours=4):
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
                    'numberOfResults': 5
                }
            }
        )
        
        # Extract retrieved passages
        retrieved_passages = [result['content']['text'] for result in retrieve_response['retrievalResults']]
        context = "\n\n".join(retrieved_passages)
        
        # If a Lambda function is specified, retrieve its logs and add to context
        if lambda_function:
            print(f"Retrieving logs for Lambda function '{lambda_function}' from the last {hours} hours...")
            lambda_logs = get_logs_for_function(lambda_function, hours)
            context += f"\n\nRecent Lambda function logs for '{lambda_function}':\n{lambda_logs}"
        
        # If no prompt is provided, construct a default one
        if prompt is None:
            prompt = f"""
            Context information:
            {context}
            
            Question: {query_text}
            
            Please answer the question based on the context provided.
            """
        else:
            # If a prompt is provided, inject the context into it
            prompt = prompt.replace("{context}", context)
        
        # Call the Bedrock model with the constructed prompt
        response = bedrock_runtime.invoke_model_with_response_stream(
            modelId=model_id,
            body=json.dumps({
                "prompt": prompt,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_gen_len": 512
            })
        )
        
        return response
        
    except ClientError as e:
        print(f"Error in retrieve and generate: {e}")
        return None

region_name = 'us-east-1'
kb_id = '3JVFPNMRFR'
model_id = 'meta.llama3-8b-instruct-v1:0'
lambda_function = 'volatileApp'  # The Lambda function to retrieve logs from
hours = 4  # Number of hours of logs to retrieve

@app.route("/", methods=["GET"])
def home():
    data = request.get_json()
    def generate():
        # query_value = data.get('query', 'No query provided') if data else 'No query provided'
        if "query" in data:
            prompt = data.get("prompt", None)
            rag_response_stream = retrieve_and_generate(region_name, kb_id, model_id, data["query"], prompt, lambda_function, hours)
            # print(f"rag res stream: {rag_response_stream}")
            for event in rag_response_stream["body"]:
                chunk = event["chunk"]
                if chunk:
                    yield f"{json.loads(chunk["bytes"].decode())["generation"]}"
        # yield f"data: Query value: {query_value}\n\n"

    return Response(generate(), content_type='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True)
