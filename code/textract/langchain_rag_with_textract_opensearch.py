import langchain
import boto3
from urllib.request import urlretrieve
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
import utils


#load environment variables
load_dotenv(find_dotenv())

#initialize variables
session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1')
identity = session.client('sts').get_caller_identity()['Arn']
credentials = session.get_credentials()
service = 'aoss'
region_name = 'us-east-1'
# auth = AWSV4SignerAuth(credentials, service, region_name)
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region_name, service, session_token=credentials.token)
vector_store_name = 'textract-bedrock-opensearch-rag'
index_name = "textract-bedrock-opensearch-rag-index"
encryption_policy_name = "textract-bedrock-opensearch-sp"
network_policy_name = "textract-bedrock-opensearch-np"
access_policy_name = 'textract-bedrock-opensearch-ap'
bucket = 'sagemaker-ca-central-1-137360334857'
key = 'textract-demo/AKash test_report_0000.pdf'

#initialize llm and other required clients
llm = Bedrock(client=bedrock_client, model_id="anthropic.claude-v2", model_kwargs={"max_tokens_to_sample": 200})
embeddings = BedrockEmbeddings(client=bedrock_client,model_id="amazon.titan-embed-text-v1")
aoss_client = session.client('opensearchserverless',region_name='us-east-1')
s3 = session.client('s3',region_name='ca-central-1')
textract = session.client('textract',region_name='ca-central-1')

#python code to check if file exists in S3
response = s3.list_objects(Bucket=bucket, Prefix=key)
if 'Contents' in response:
    print("File exists in S3")
    # print(s3.get_object(Bucket=bucket, Key=key))


def extract_text(response: dict, extract_by="LINE") -> list:
    text = []
    for block in response["Blocks"]:
        if block["BlockType"] == extract_by:
            text.append(block["Text"])
    return text

# #python code to send s3 file to Amazon textract

def extract_text_using_textract(bucket, key):

    response = textract.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )
    return response

# print(response)
# #python code to convert json to text
response = extract_text_using_textract(bucket, key)
text = extract_text(response)
# print(type(text))

#python code to convert text list to string 
text = " ".join(text)

#python code to split text into chunks using recrusive character text splitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_text(text)
print(f'Split {len(text)} documents into {len(docs)} chunks.')

#Print the chunks
# for i, doc in enumerate(docs):
#     print(f'Chunk {i}: {doc}')

create_network_policy = utils.create_network_policy(aoss_client, network_policy_name, vector_store_name, type='network')
print(f'Network Policy is {create_network_policy}')

create_encryption_policy = utils.create_encryption_policy(aoss_client, encryption_policy_name, vector_store_name, type='encryption')
print(f'Encryption Policy is {create_encryption_policy}')

create_collection_status = utils.create_collection(aoss_client, vector_store_name,type='VECTORSEARCH')
print(f'Collection Status is {create_collection_status}')

# create access policy
create_access_policy = utils.create_access_policy(aoss_client, access_policy_name, vector_store_name, type='data', identity=identity)
print(f'Access Policy is {create_access_policy}')

status, collection_id, openSearch_host = utils.get_collection_status(aoss_client,vector_store_name,region_name)
print(f"Collection Status is {status}, Collection_id is {collection_id}, Collection host is {openSearch_host}")

# docs_search = utils.store_data_from_texts(docs, embeddings, openSearch_host, index_name, awsauth)
docs_search = utils.get_opensearch_client(embeddings, openSearch_host, index_name, awsauth)

# # qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(llm=llm, chain_type="stuff", 
#                                                                retriever=docs_search.as_retriever(search_kwargs={'k':3}),
#                                                                return_source_documents=True)
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docs_search.as_retriever())

query = "What are the Covid 19 Results for this patient?"
# result = qa.invoke({"query": query})
# print(result)
# print(result['result'])


prompt_template = """Human: Use the following pieces of context to provide a concise answer in Engish to the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Assistant:"""

PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

qa_prompt = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=docs_search.as_retriever(),
    # return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT},
)
result = qa_prompt({"query": query})
print(result['result'])
