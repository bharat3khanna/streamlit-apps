import langchain
import json
import os
import sys
import boto3
#import botocore

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock',region_name='us-east-1') 
#code for listing bedrock models
response = bedrock_client.list_foundation_models()
#print(response)
models = response['modelSummaries']

for model in models:
   modelName = model['modelName']
   provider = model['providerName']
   status = model['modelLifecycle']['status']
   print(f"Model: {modelName}, Provider: {provider}, Status: {status}")
   