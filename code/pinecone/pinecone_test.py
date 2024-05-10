#from pinecone import Pin
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

import pinecone
import time
import os


load_dotenv()

# add index name from pinecone.io
index_name = "docs-quickstart-index"
# add Pinecone API key from app.pinecone.io
api_key = os.environ.get("PINECONE_API_KEY")
env = os.environ.get("PINECONE_ENV")

# api_key="7c35f5e7-c9d0-4a8b-915d-068a486a939f"
# env="us-east-1"

pc = Pinecone(api_key=api_key)

print(api_key, env)

# pinecone.init(api_key=api_key,environment=env)
# pinecone.init(api_key=api_key)

# if index_name not in pinecone.list_indexes():
#     pinecone.create_index(index_name, dimension=1536,metric="dotproduct")

# while not pinecone.describe_index(index_name)['status'] == 'ready':
#     time.sleep(1)


# index = pinecone.Index(index_name)
# index.describe_index()

# index_name = "docs-quickstart-index"
index_name = "test3"

# List all indexes in your project
indexes = pc.list_indexes()

# Check if your specific index exists

#insert a try catch block to check if index exists
try:
    index = pc.Index(index_name)
    if index:
        print("Index exists.")
except pinecone.PineconeException as e:
    print("Index does not exist. Creating Index")
    # print(e)

# index = pc.Index(index_name)
# if index:
#     print("Index exists.")
# else:
#     print("Index does not exist.")
# if index_name in pc.list_indexes():
#     print("Index already exists")
# else:
#     print("Index does not exist")
#     print(indexes)
    pc.create_index(
    name=index_name,
    dimension=8,
    metric="dotproduct",
    spec=ServerlessSpec(
        cloud='aws', 
        region='us-east-1'
    ) 
)
