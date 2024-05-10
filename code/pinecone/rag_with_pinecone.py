import langchain
import boto3
import os
import botocore
from urllib.request import urlretrieve
from pypdf import PdfReader, PdfWriter
import glob
import numpy as np
from pinecone import Pinecone, ServerlessSpec
import pinecone
import time
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain_community.chat_models import BedrockChat
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from dotenv import load_dotenv
from langchain.vectorstores import Pinecone as PineconeStore

#load environment variables
load_dotenv()

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1') 

llm = BedrockChat(client=bedrock_client,model_id="anthropic.claude-v2",model_kwargs={"max_tokens_to_sample": 200})
embeddings = BedrockEmbeddings(client=bedrock_client,model_id="amazon.titan-embed-text-v1")
# embeddings.embed_query("hello world")
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

# avg_doc_length = lambda documents: sum([len(doc.page_content) for doc in documents])//len(documents)
# print(f'Average length among {len(documents)} documents loaded is {avg_doc_length(documents)} characters.')
# print(f'After the split we have {len(docs)} documents as opposed to the original {len(documents)}.')
# print(f'Average length among {len(docs)} documents (after split) is {avg_doc_length(docs)} characters.')

# print(docs[0])
# print(docs[0].metadata)
print(docs[0].page_content)
sample_embedding = np.array(embeddings.embed_query(docs[0].page_content))
#sample_embedding = embeddings.embed_query(docs[0].page_content)
print('Sample embedding of a document chunk:',sample_embedding)
print('Sample embedding shape:', sample_embedding.shape)
print('Sample embedding dtype:', sample_embedding.dtype)


# Adding to Pinecone
index_name = 'aws-shareholder-genai-test'
# add Pinecone API key from app.pinecone.io
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)

try:
    index = pc.Index(index_name)
    if index:
        print("Index exists.")
except Exception as e:
    print("Index does not exist. Creating Index")
    pc.create_index(
    name=index_name,
    dimension=sample_embedding.shape[0],
    metric="dotproduct",
    spec=ServerlessSpec(
        cloud='aws', 
        region='us-east-1'
    ) 
    )   

index = pc.Index(index_name)
print(index.describe_index_stats())

docsearch = PineconeStore.from_documents(docs, embeddings, index_name=index_name)
# print(index.describe_index_stats())

# text_field = "text"
# #print(docs[0])
# vectorstore = PineconeStore(index,embeddings,text_field)


