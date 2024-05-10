import langchain
import boto3
import os
import botocore
from urllib.request import urlretrieve
from pypdf import PdfReader, PdfWriter
import glob
import numpy as np

import time
import json
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain_community.chat_models import BedrockChat
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from dotenv import load_dotenv, find_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from langchain.vectorstores import OpenSearchVectorSearch
from requests_aws4auth import AWS4Auth
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate



#load environment variables
load_dotenv(find_dotenv())

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1')
identity = session.client('sts').get_caller_identity()['Arn']
credentials = session.get_credentials()
service = 'aoss'
region_name = 'us-east-1'
# auth = AWSV4SignerAuth(credentials, service, region_name)
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region_name, service, session_token=credentials.token)

vector_store_name = 'bedrock-workshop-rag'
index_name = "bedrock-workshop-rag-index"
encryption_policy_name = "bedrock-workshop-rag-sp"
network_policy_name = "bedrock-workshop-rag-np"
access_policy_name = 'bedrock-workshop-rag-ap'

# llm = BedrockChat(client=bedrock_client,model_id="anthropic.claude-v2",model_kwargs={"max_tokens_to_sample": 200})
llm = Bedrock(client=bedrock_client, model_id="anthropic.claude-v2", model_kwargs={"max_tokens_to_sample": 200})
embeddings = BedrockEmbeddings(client=bedrock_client,model_id="amazon.titan-embed-text-v1")
aoss_client = session.client('opensearchserverless',region_name='us-east-1')


# Define the directory path here
directory = './data'  

# Check if the directory already exists
if not os.path.exists(directory):
    os.makedirs(directory)


urls = [
    'https://s2.q4cdn.com/299287126/files/doc_financials/2023/ar/2022-Shareholder-Letter.pdf',
    'https://s2.q4cdn.com/299287126/files/doc_financials/2022/ar/2021-Shareholder-Letter.pdf',
    'https://s2.q4cdn.com/299287126/files/doc_financials/2021/ar/Amazon-2020-Shareholder-Letter-and-1997-Shareholder-Letter.pdf',
    'https://s2.q4cdn.com/299287126/files/doc_financials/2020/ar/2019-Shareholder-Letter.pdf'
]

filenames = [
    'AMZN-2022-Shareholder-Letter.pdf',
    'AMZN-2021-Shareholder-Letter.pdf',
    'AMZN-2020-Shareholder-Letter.pdf',
    'AMZN-2019-Shareholder-Letter.pdf'
]

metadata = [
    dict(year=2022, source=filenames[0]),
    dict(year=2021, source=filenames[1]),
    dict(year=2020, source=filenames[2]),
    dict(year=2019, source=filenames[3])]

data_root = "./data/"

for idx, url in enumerate(urls):
    try:
        urlretrieve(url, data_root + filenames[idx])
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

pdfs = glob.glob(data_root + '*.pdf')
for pdf in pdfs:
    reader = PdfReader(pdf)
    writer = PdfWriter()
    for pagnum in range(len(reader.pages)-3):
        page = reader.pages[pagnum]
        writer.add_page(page)
    with open(pdf, 'wb') as f:
        f.seek(0)
        writer.write(f)
        f.truncate()


#write a code to load documents to langchain using pypdfloader
documents = []
for idx, file in enumerate(filenames):
    loader = PyPDFLoader(data_root + file)
    docs = loader.load()
    for doc in docs:
        doc.metadata = metadata[idx]
    print(f"Loaded {len(docs)} documents from {file}")
    documents.extend(docs)   

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_documents(documents)
print(f'Split {len(documents)} documents into {len(docs)} chunks.')

def create_collection(name, type):
   
    try:
        response = aoss_client.create_collection(name=name,type=type)

    except:
        print("Collection already exists")
        # response = aoss_client.delete_collection(name=vector_store_name)
        # response = aoss_client.create_collection(name=vector_store_name, type='VECTORSEARCH')
        
    else: 
        print("Collection created")
   
def get_collection_status(name):
    while True:
        response = aoss_client.batch_get_collection(names=[name]) 
        collection_details = response['collectionDetails'][0]
        status = collection_details['status']
        host = collection_details['collectionEndpoint']
        collection_id = collection_details['id']
        openSearch_host = 'http://'+collection_id+'.'+region_name+'.aoss.amazonaws.com:443'
        # print(f"Collection status is: {status}")

        # .get_collection(name=vector_store_name)
        if status == 'ACTIVE':
            print("Collection is active")
            print(f"Collection host is: {host}")
            break
        time.sleep(5)
    return status, host, collection_id, openSearch_host


try:
   response = aoss_client.get_access_policy(name=access_policy_name,type='data')
except aoss_client.exceptions.ResourceNotFoundException:
   print("Access Policy does not exist")
   access_policy = aoss_client.create_access_policy(
    name = access_policy_name,
    policy = json.dumps(
        [
            {
                'Rules': [
                    {
                        'Resource': ['collection/' + vector_store_name],
                        'Permission': [
                            'aoss:CreateCollectionItems',
                            'aoss:DeleteCollectionItems',
                            'aoss:UpdateCollectionItems',
                            'aoss:DescribeCollectionItems'],
                        'ResourceType': 'collection'
                    },
                    {
                        'Resource': ['index/' + vector_store_name + '/*'],
                        'Permission': [
                            'aoss:CreateIndex',
                            'aoss:DeleteIndex',
                            'aoss:UpdateIndex',
                            'aoss:DescribeIndex',
                            'aoss:ReadDocument',
                            'aoss:WriteDocument'],
                        'ResourceType': 'index'
                    }],
                'Principal': [identity],
                'Description': 'Easy data policy'}
        ]),
    type = 'data'
)
else:
  print("Policy already exists")

# host = collection['createCollectionDetail']['id'] + '.' + os.environ.get("AWS_DEFAULT_REGION", None) + '.aoss.amazonaws.com:443'
print(f"openSearch_host is {openSearch_host}")
print(f"Indexing {len(docs)} documents into {index_name}...")


docsearch = OpenSearchVectorSearch.from_documents(
    docs, 
    embeddings, 
    opensearch_url=openSearch_host,
    index_name=index_name,
    http_auth=awsauth,
    connection_class=RequestsHttpConnection,
    engine='faiss',
    timeout = 100,
    verify_certs = True,
    use_ssl = True
)

query = "How has AWS evolved?"
# results = docsearch.similarity_search(query,k=3)
# print(results)
# print(results[0].page_content)
# print(results[0].metadata)


qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())
qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(llm=llm, chain_type="stuff", 
                                                              retriever=docsearch.as_retriever(search_kwargs={'k':3}),
                                                              return_source_documents=True)
# print(qa.run(query))
# print(qa_with_sources(query))

prompt_template = """Human: Use the following pieces of context to provide a concise answer in Italian to the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Assistant:"""

PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

qa_prompt = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=docsearch.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT},
)
result = qa_prompt({"query": query})
print(result['result'])




