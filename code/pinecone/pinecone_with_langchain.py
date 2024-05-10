# from langchain_pinecone import PineconeVectorStore
import pinecone
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os
from langchain.embeddings import BedrockEmbeddings, OpenAIEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain_community.chat_models import BedrockChat
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_community.vectorstores.pinecone import Pinecone as PineconeStore
from langchain.vectorstores import Pinecone as PineconeVectorStore
   
from dotenv import load_dotenv
import boto3

load_dotenv()

api_key = os.environ.get("PINECONE_API_KEY")
env = os.environ.get("PINECONE_ENV")

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1') 
#bedrock_client = session.client('bedrock',region_name='us-east-1')

llm = BedrockChat(client=bedrock_client,model_id="anthropic.claude-v2",model_kwargs={"max_tokens_to_sample": 200})

bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1",credentials_profile_name='dev',region_name='us-east-1')

embeddings = OpenAIEmbeddings()
# embedding_fn = bedrock_embeddings.embed_documents()


data_root = "./data/"

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

pc = Pinecone(api_key=api_key)

index_name = "aws-shareholder-genai-test"
# print(docs)
# dim = 1536

# if index_name not in pc.list_indexes().names():
# #   pinecone.create_index(name=index_name, dimension=dim)
#       print("Index does not exist. Creating Index")
#       pc.create_index(
#         name=index_name,
#         dimension=8,
#         metric="dotproduct",
#         spec=ServerlessSpec(
#             cloud='aws', 
#             region='us-east-1'
#         ) 
# )
# else:
#       print("Index exists")
#       print(pc.describe_index(index_name))


index = pc.Index(index_name)
print(index.describe_index_stats())
# index = pinecone.Index(index_name)
# text_field = "text"
# vectorstore = PineconeStore(index, embeddings, text_field)
#from langchain.vectorstores import Pinecone as PineconeStore 
PineconeVectorStore

docsearch = PineconeStore.from_documents(docs, embeddings, index_name=index_name)
# docsearch = PineconeVectorStore.from_documents(docs, embeddings, index_name=index_name)
# index = PineconeStore.Index(index_name)
# pc_interface = PineconeStore.from_existing_index(
#   index_name,
#   embedding=embeddings,
#   namespace="default"
# )

# index.upsert()

# pcs = PineconeStore(api_key=api_key)
#vectorstore = PineconeVectorStore(index_name, embeddings)
# vectorstore_from_docs = PineconeVectorStore.from_documents(docs, embeddings, index_name=index_name)
# vectorstore_from_docs = pcs.from_documents(docs, embeddings, index_name=index_name)

# query = "How has AWS evolved?"
# vectorstore.similarity_search(query, k=2)


