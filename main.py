import boto3
import json
from botocore.exceptions import ClientError

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
                    'numberOfResults': 5
                }
            }
        )
        
        # Extract retrieved passages
        retrieved_passages = [result['content']['text'] for result in retrieve_response['retrievalResults']]
        context = "\n\n".join(retrieved_passages)
        
        # Now construct a prompt for the model
        prompt = f"""
        Context information:
        {context}
        
        Question: {query_text}
        
        Please answer the question based on the context provided.
        """
        
        # Call the Bedrock model with the constructed prompt
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "prompt": prompt,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_gen_len": 512
            })
        )
        
        # Parse and return the model's response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        return response_body['generation']
        
    except ClientError as e:
        print(f"Error in retrieve and generate: {e}")
        return None

def main():
    # Configuration
    region_name = 'us-east-1'
    kb_id = '3JVFPNMRFR'
    model_id = 'meta.llama3-8b-instruct-v1:0'
    
    # Test retrieval-augmented generation
    print("\nPerforming retrieval-augmented generation...")
    query = "What are the requirements and processes for LEI data management?"
    rag_response = retrieve_and_generate(region_name, kb_id, model_id, query)
    
    if rag_response:
        print("\nGenerated response:")
        print(rag_response)

if __name__ == "__main__":
    main()
