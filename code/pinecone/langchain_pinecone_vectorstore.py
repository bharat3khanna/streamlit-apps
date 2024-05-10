import pinecone
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv,find_dotenv
import os

load_dotenv(find_dotenv())

api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key="478fe870-87df-4f95-bb6e-9c3297013141")

index_name = "aws-shareholder-genai-test"
index = pc.Index(index_name)

from langchain.vectorstores import Pinecone
vectorstore = PineconeVectorStore(index)

