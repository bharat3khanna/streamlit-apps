import boto3
import time
import json
from dotenv import load_dotenv, find_dotenv
import os

#load environment variables
load_dotenv(find_dotenv())

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1') 
identity = session.client('sts').get_caller_identity()['Arn']
print(identity)

vector_store_name = 'bedrock-workshop-rag'
index_name = "bedrock-workshop-rag-index"
encryption_policy_name = "bedrock-workshop-rag-sp"
network_policy_name = "bedrock-workshop-rag-np"
access_policy_name = 'bedrock-workshop-rag-ap'
# identity = boto3.client('sts').get_caller_identity()['Arn']

aoss_client = session.client('opensearchserverless',region_name='us-east-1')
# aoss_client = session.client('opensearchserverless',region_name='ca-central-1')
# # security_policy = aoss_client.create_security_policy(
# #     name = encryption_policy_name,
# #     policy = json.dumps(
# #         {
# #             'Rules': [{'Resource': ['collection/' + vector_store_name],
# #             'ResourceType': 'collection'}],
# #             'AWSOwnedKey': True
# #         }),
# #     type = 'encryption'
# # )

try:
    response = aoss_client.create_collection(name=vector_store_name,type='VECTORSEARCH')

except:
    print("Collection already exists, Dropping and recreating collection")
    list_collections_response = aoss_client.list_collections(maxResults=10,
    collectionFilters={'name': vector_store_name})
    collection_summaries = list_collections_response.get('collectionSummaries')
    # process collection summaries
    if collection_summaries:
        collection_id = list_collections_response['collectionSummaries'][0]['id']
        print(f'collection name {vector_store_name} already exists with collection id {collection_id}. Deleting and creating collection again')
        delete_collection_response = aoss_client.delete_collection(id=collection_id)
        print(f'Collection {vector_store_name} deleted')
        time.sleep(10)
        print(f'Creating Collection {vector_store_name}')
        create_collection_response = aoss_client.create_collection(name=vector_store_name, type='VECTORSEARCH')

        while True:
            response = aoss_client.batch_get_collection(names=[vector_store_name]) 
            collection_details = response['collectionDetails'][0]
            status = collection_details['status']
            host = collection_details['collectionEndpoint']
            print(f"Collection status is: {status}")

            # .get_collection(name=vector_store_name)
            if status == 'ACTIVE':
                print("Collection is active")
                print(f"Collection host is: {host}")
                break
            time.sleep(5)
        # 
        # print(f'Collection {vector_store_name} Created')
else: 
    print("Collection created")

# # network_policy = aoss_client.create_security_policy(
# #     name = network_policy_name,
# #     policy = json.dumps(
# #         [
# #             {'Rules': [{'Resource': ['collection/' + vector_store_name],
# #             'ResourceType': 'collection'}],
# #             'AllowFromPublic': True}
# #         ]),
# #     type = 'network'
# # )

# try:
#     response = aoss_client.create_collection(name=vector_store_name,type='VECTORSEARCH')

# except:
#     print("Collection already exists")
# else: 
#     print("Collection created")
   


# while True:
#     response = aoss_client.batch_get_collection(names=[vector_store_name]) 
#     collection_details = response['collectionDetails'][0]
#     status = collection_details['status']
#     host = collection_details['collectionEndpoint']
#     # print(f"Collection status is: {status}")

#     # .get_collection(name=vector_store_name)
#     if status == 'ACTIVE':
#         print("Collection is active")
#         print(f"Collection host is: {host}")
#         break
#     time.sleep(5)

# try:
#    response = aoss_client.get_access_policy(name=access_policy_name,type='data')
# except aoss_client.exceptions.ResourceNotFoundException:
#    print("Access Policy does not exist")
#    access_policy = aoss_client.create_access_policy(
#     name = access_policy_name,
#     policy = json.dumps(
#         [
#             {
#                 'Rules': [
#                     {
#                         'Resource': ['collection/' + vector_store_name],
#                         'Permission': [
#                             'aoss:CreateCollectionItems',
#                             'aoss:DeleteCollectionItems',
#                             'aoss:UpdateCollectionItems',
#                             'aoss:DescribeCollectionItems'],
#                         'ResourceType': 'collection'
#                     },
#                     {
#                         'Resource': ['index/' + vector_store_name + '/*'],
#                         'Permission': [
#                             'aoss:CreateIndex',
#                             'aoss:DeleteIndex',
#                             'aoss:UpdateIndex',
#                             'aoss:DescribeIndex',
#                             'aoss:ReadDocument',
#                             'aoss:WriteDocument'],
#                         'ResourceType': 'index'
#                     }],
#                 'Principal': [identity],
#                 'Description': 'Easy data policy'}
#         ]),
#     type = 'data'
# )
# else:
#   print("Policy already exists")

# # host = collection['createCollectionDetail']['id'] + '.' + os.environ.get("AWS_DEFAULT_REGION", None) + '.aoss.amazonaws.com:443'
# print(host)