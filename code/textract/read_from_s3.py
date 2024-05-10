import boto3
import json
#python code to read a file from S3

session = boto3.Session(profile_name='dev')
bedrock_runtime = session.client('bedrock-runtime',region_name='us-east-1')


s3 = session.client('s3',region_name='ca-central-1')
textract = session.client('textract',region_name='ca-central-1')
bucket = 'sagemaker-ca-central-1-137360334857'
key = 'textract-demo/AKash test_report_0000.pdf'

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
print(text)

