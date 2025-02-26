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
                "temperature": 0.2,  # Even lower temperature for more deterministic responses
                "top_p": 0.9,
                "max_gen_len": 150   # Further reduced max length
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
        print(f"Error in retrieve and generate: {e}")
        return None

def main():
    # Configuration
    region_name = 'us-east-1'
    kb_id = '3JVFPNMRFR'
    model_id = 'meta.llama3-8b-instruct-v1:0'
    
    print("\n===== Welcome to ProdPal =====")
    print("Your AI assistant for answering questions about products and services.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        # Get user input for the query
        query = input("Ask ProdPal a question: ")
        
        # Check if user wants to exit
        if query.lower() in ['exit', 'quit']:
            print("Thank you for using ProdPal. Goodbye!")
            break
        
        print("\nProdPal is thinking...")
        rag_response = retrieve_and_generate(region_name, kb_id, model_id, query)
        
        if rag_response:
            print("\nProdPal's response:")
            print(rag_response)
            print("\n" + "-" * 50 + "\n")
        else:
            print("\nSorry, I couldn't generate a response. Please try again.")
            print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    main()
