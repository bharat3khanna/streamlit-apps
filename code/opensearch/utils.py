import glob
from pypdf import PdfReader, PdfWriter
import os
from urllib.request import urlretrieve
import botocore
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import json
from langchain.vectorstores import OpenSearchVectorSearch
from opensearchpy import RequestsHttpConnection

def delete_last_three_pages(directory):
    directory = os.getcwd() + "\\" + str(directory)+"\\"
    print(f'Deleting last 3 pages from the files at Path : {directory}')
    pdfs = glob.glob(directory + '*.pdf')
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

def download_data(directory,urls,filenames):

    directory = os.getcwd() + "\\" + str(directory)+"\\"
    print(f'Downloading files at Path : {directory}')
    # Check if the directory already exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # data_root = "./data/"

    for idx, url in enumerate(urls):
        try:
            urlretrieve(url, directory + filenames[idx])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist.")
            else:
                raise

def chunk_data(directory,metadata):
    # data_root = "./data/"
    directory = os.getcwd() + "\\" + str(directory)+"\\"
    print(f'Chunking the data from the files at Path : {directory}')
    filenames = glob.glob(directory + '*.pdf')

#write a code to load documents to langchain using pypdfloader
    documents = []
    for idx, file in enumerate(filenames):
        loader = PyPDFLoader(file)
        docs = loader.load()
        for doc in docs:
            doc.metadata = metadata[idx]
        print(f"Loaded {len(docs)} documents from {file}")
        documents.extend(docs)   

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    print(f'Split {len(documents)} documents into {len(docs)} chunks.')
    return docs

def create_collection(aoss_client, name, type):
    status = ""
    try:
        response = aoss_client.create_collection(name=name,type=type)

    except:
        print("Collection already exists")
        # response = aoss_client.delete_collection(name=vector_store_name)
        # response = aoss_client.create_collection(name=vector_store_name, type='VECTORSEARCH')
        status = "ACTIVE"    
    else: 
        print("Collection created")
        status = "CREATED"
    return status

def get_collection_status(aoss_client,name,region_name):
    while True:
        response = aoss_client.batch_get_collection(names=[name]) 
        collection_details = response['collectionDetails'][0]
        status = collection_details['status']
        host = collection_details['collectionEndpoint']
        collection_id = collection_details['id']
        openSearch_host = 'http://'+collection_id+'.'+region_name+'.aoss.amazonaws.com:443'
        # print(f"Collection status is: {status}")

        # .get_collection(name=vector_store_name)
        if status == 'ACTIVE':
            print("Collection is active")
            print(f"Collection host is: {host}")
            break
        time.sleep(5)
    return status, collection_id, openSearch_host

def create_access_policy(aoss_client,access_policy_name, vector_store_name, type, identity):
    
    try:
        response = aoss_client.get_access_policy(name=access_policy_name,type=type)
    except aoss_client.exceptions.ResourceNotFoundException:
        print("Access Policy does not exist. Creating Acecss Policy")
        access_policy = aoss_client.create_access_policy(
            name = access_policy_name,
            policy = json.dumps(
                [
                    {
                        'Rules': [
                            {
                                'Resource': ['collection/' + vector_store_name],
                                'Permission': [
                                    'aoss:CreateCollectionItems',
                                    'aoss:DeleteCollectionItems',
                                    'aoss:UpdateCollectionItems',
                                    'aoss:DescribeCollectionItems'],
                                'ResourceType': 'collection'
                            },
                            {
                                'Resource': ['index/' + vector_store_name + '/*'],
                                'Permission': [
                                    'aoss:CreateIndex',
                                    'aoss:DeleteIndex',
                                    'aoss:UpdateIndex',
                                    'aoss:DescribeIndex',
                                    'aoss:ReadDocument',
                                    'aoss:WriteDocument'],
                                'ResourceType': 'index'
                            }],
                        'Principal': [identity],
                        'Description': 'Easy data policy'}
                ]),
            type = 'data'
    )
    else:
        print("Access Policy already exists")

def store_data(docs, embeddings, opensearch_url, index_name, awsauth):
    print(f"Indexing {len(docs)} documents into {index_name}...")

    docsearch = OpenSearchVectorSearch.from_documents(
        docs, 
        embeddings, 
        opensearch_url=opensearch_url,
        index_name=index_name,
        http_auth=awsauth,
        connection_class=RequestsHttpConnection,
        engine='faiss',
        timeout = 100,
        verify_certs = True,
        use_ssl = True
    )
    return docsearch