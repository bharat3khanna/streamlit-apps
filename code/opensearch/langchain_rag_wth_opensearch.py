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
# docs_search = OpenSearchVectorSearch()


# Define the directory path here
directory = 'data'  
filenames = [
        'AMZN-2022-Shareholder-Letter.pdf',
        'AMZN-2021-Shareholder-Letter.pdf',
        'AMZN-2020-Shareholder-Letter.pdf',
        'AMZN-2019-Shareholder-Letter.pdf'
    ]

urls = [
        'https://s2.q4cdn.com/299287126/files/doc_financials/2023/ar/2022-Shareholder-Letter.pdf',
        'https://s2.q4cdn.com/299287126/files/doc_financials/2022/ar/2021-Shareholder-Letter.pdf',
        'https://s2.q4cdn.com/299287126/files/doc_financials/2021/ar/Amazon-2020-Shareholder-Letter-and-1997-Shareholder-Letter.pdf',
        'https://s2.q4cdn.com/299287126/files/doc_financials/2020/ar/2019-Shareholder-Letter.pdf'
]

metadata = [
        dict(year=2022, source=filenames[0]),
        dict(year=2021, source=filenames[1]),
        dict(year=2020, source=filenames[2]),
        dict(year=2019, source=filenames[3])]

#download the existing data
download_data =  utils.download_data(directory, urls, filenames)

#delete last 3 pages for each file
delete_data = utils.delete_last_three_pages(directory)

# #chunk the data
docs = utils.chunk_data(directory,metadata)

# create collection
create_collection_status = utils.create_collection(aoss_client, vector_store_name,type='VECTORSEARCH')
print(f'Collection Status is {create_collection_status}')

# #get collection status
status, collection_id, openSearch_host = utils.get_collection_status(aoss_client,vector_store_name,region_name)
print(f"Collection Status is {status}, Collection_id is {collection_id}, Collection host is {openSearch_host}")

# create access policy
create_access_policy = utils.create_access_policy(aoss_client, access_policy_name, vector_store_name, type='data', identity=identity)

# #store data in collection
if docs_search:
    print("Data is already stored in collection")
else:
    docs_search = utils.store_data(docs, embeddings, openSearch_host, index_name, awsauth)




# # host = collection['createCollectionDetail']['id'] + '.' + os.environ.get("AWS_DEFAULT_REGION", None) + '.aoss.amazonaws.com:443'
# print(f"openSearch_host is {openSearch_host}")
# print(f"Indexing {len(docs)} documents into {index_name}...")

# query = "How has AWS evolved?"
# # results = docsearch.similarity_search(query,k=3)
# # print(results)
# # print(results[0].page_content)
# # print(results[0].metadata)


# qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())
qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(llm=llm, chain_type="stuff", 
                                                               retriever=docs_search.as_retriever(search_kwargs={'k':3}),
                                                               return_source_documents=True)
# # print(qa.run(query))
# # print(qa_with_sources(query))

# prompt_template = """Human: Use the following pieces of context to provide a concise answer in Italian to the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

# {context}

# Question: {question}
# Assistant:"""

# PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

# qa_prompt = RetrievalQA.from_chain_type(
#     llm=llm,
#     chain_type="stuff",
#     retriever=docsearch.as_retriever(),
#     return_source_documents=True,
#     chain_type_kwargs={"prompt": PROMPT},
# )
# result = qa_prompt({"query": query})
# print(result['result'])




