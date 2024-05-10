import boto3

session = boto3.Session(profile_name='dev')
opensearch_client = session.client('opensearchserverless', region_name='us-east-1')

# Create a security policy 
response = opensearch_client.create_security_policy(
  Name='my-policy',
  Type='access', 
  Policy='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"*"},"Action":"es:*", "Resource":"*"}]}')

# Create a collection
# response = opensearch_client.create_collection(
#   Name='my-collection',
#   SecurityPolicyName='my-policy'  
# )


response = opensearch_client.create_collection(
  Name='my-collection',
  SecurityPolicyName='my-policy'  
)

