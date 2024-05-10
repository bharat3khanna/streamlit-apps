import langchain
import boto3
import os
import botocore
from urllib.request import urlretrieve
from pypdf import PdfReader, PdfWriter
import glob
import numpy as np
# from langchain.embeddings import BedrockEmbeddings
from langchain_community.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain_community.chat_models import BedrockChat
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1') 

llm = BedrockChat(client=bedrock_client,model_id="anthropic.claude-v2",model_kwargs={"max_tokens_to_sample": 200})
embeddings = BedrockEmbeddings(client=bedrock_client,model_id="amazon.titan-embed-text-v1")
# embeddings = BedrockEmbeddings(client=bedrock_client, model_id="anthropic.claude-v2")
# embeddings.embed_query("hello world")

# - create the Anthropic Model
# llm = BedrockChat(
#     model_id="anthropic.claude-v2", 
#     client=bedrock_client, 
#     model_kwargs={"max_tokens_to_sample": 200}
# )
# embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1",
                                    #    client=bedrock_client)


sample_embedding = np.array(embeddings.embed_query("hello world"))
print("Sample embedding of a document chunk: ", sample_embedding)
print("Size of the embedding: ", sample_embedding.shape)