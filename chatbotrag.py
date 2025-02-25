import faiss
import numpy as np
import json
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = "TRUE"
os.environ['OMP_NUM_THREADS'] = "1"

openai_keys = json.load(open('hackathon_openai_keys.json'))
my_openai_key = openai_keys['team_1']

from openai import OpenAI
client = OpenAI(api_key=my_openai_key)

# data = np.random.random((1000, 512)).astype('float32')
dimension = 384
index = faiss.IndexFlatL2(dimension)
# index.add(data)

from transformers import AutoTokenizer, AutoModel, pipeline
import torch
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

def embed_text(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1)
        return embeddings.numpy()
    
documents = ["""The Vanguard Group, Inc. is an American registered investment advisor founded on May 1, 1975, and based in Malvern, Pennsylvania, with about $10.4 trillion in global assets under management as of November 2024.[3] It is the largest provider of mutual funds and the second-largest provider of exchange-traded funds (ETFs) in the world after BlackRock's iShares.[4] In addition to mutual funds and ETFs, Vanguard offers brokerage services, educational account services, financial planning, asset management, and trust services. Several mutual funds managed by Vanguard are ranked at the top of the list of US mutual funds by assets under management.[5] Along with BlackRock and State Street, Vanguard is considered to be one of the Big Three index fund managers that play a dominant role in retail investing.[6][7]

Founder and former chairman John C. Bogle is credited with the creation of the first index fund available to individual investors and was a proponent and major enabler of low-cost investing by individuals,[8][9] though Rex Sinquefield has also been credited with the first index fund open to the public a few years before Bogle.[10]

Vanguard is owned by the funds managed by the company and is therefore owned by its customers.[11] Vanguard offers two classes of most of its funds: investor shares and admiral shares. Admiral shares have slightly lower expense ratios but require a higher minimum investment, often between $3,000 and $100,000 per fund.[12] Vanguard's corporate headquarters is in Malvern, a suburb of Philadelphia. It has satellite offices in Charlotte, North Carolina, Dallas, Texas, Washington D.C., and Scottsdale, Arizona, as well as Canada, Australia, Asia, and Europe."""]

document_embeddings = np.vstack([embed_text(doc) for doc in documents])
# print("@@@@@@@@@@@@@@@@@@@ ", document_embeddings.shape)

index.add(document_embeddings)

print("embedding is done")

def retrive_documents(query, index, k=5):
    query_embedding = embed_text(query)
    distances, indices = index.search(query_embedding, k)
    return [documents[i] for i in indices[0]]


def generate_response(query, index):
    print("My Question : ", query)
    retrieved_docs = retrive_documents(query, index)
    context = " ".join(retrieved_docs)
    prompt = f"Context: {context}\n\nUser : {query}\nBot:"
    response = client.chat.completions.create(
    model="gpt-4",
    messages = [
        {"role":"system", "content":"You are helpful assistant."},
        {"role":"user", "content": prompt}]

    )
    # response = openai.Completion.create(engine="text-davinci-003",
    #  prompt = prompt,
    #  max_token= 250, 
    #  n = 1,
    #  stop = None,
    #  temperature=0.7)
    return response.choices[0].message.content

query = "Where is Vanguard"
response = generate_response(query, index)
print("Response : ", response)
