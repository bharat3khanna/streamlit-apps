#write a code for building a streamlit app for uploading the file to S3
import streamlit as st
import boto3
import gc
import base64
from botocore.exceptions import NoCredentialsError
from streamlit_pdf_viewer import pdf_viewer
from requests_aws4auth import AWS4Auth
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import utils


access_key = st.secrets["AWS_ACCESS_KEY_ID"]
secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
bucket_name = st.secrets["AWS_BUCKET_NAME"]
region = st.secrets["AWS_DEFAULT_REGION"]
container_pdf, container_chat = st.columns([50, 50])

session = boto3.Session(aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key, region_name=region)

bedrock_client = session.client('bedrock-runtime',region_name='us-east-1')
identity = session.client('sts').get_caller_identity()['Arn']
credentials = session.get_credentials()
service = 'aoss'
# region_name = 'us-east-1'
# auth = AWSV4SignerAuth(credentials, service, region_name)
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
vector_store_name = 'textract-bedrock-opensearch-rag'
index_name = "textract-bedrock-opensearch-rag-index"
encryption_policy_name = "textract-bedrock-opensearch-sp"
network_policy_name = "textract-bedrock-opensearch-np"
access_policy_name = 'textract-bedrock-opensearch-ap'
bucket = 'sagemaker-ca-central-1-137360334857'




llm = Bedrock(client=bedrock_client, model_id="anthropic.claude-v2", model_kwargs={"max_tokens_to_sample": 200})
embeddings = BedrockEmbeddings(client=bedrock_client,model_id="amazon.titan-embed-text-v1")
aoss_client = session.client('opensearchserverless',region_name=region)
s3 = session.client('s3',region_name='ca-central-1')
textract = session.client('textract',region_name='ca-central-1')
memory = ConversationBufferMemory()

prompt_template = """Human: Use the following pieces of context to provide a concise answer in Engish to the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Assistant:"""

PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

prompt_template_with_sources = """Human: Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES"). 
    If you don't know the answer, just say that you don't know. Don't try to make up an answer.
    ALWAYS return a "SOURCES" part in your answer.

    QUESTION: {question}
    =========
    {summaries}
    =========
    FINAL ANSWER : 
"""

PROMPT_WITH_SOURCES = PromptTemplate(template=prompt_template_with_sources, input_variables=["summaries", "question"])

#create a function to upload the file to S3
def upload_to_s3(file):
    s3 = boto3.client('s3', aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key, region_name=region)

    try:
        s3.upload_fileobj(file, bucket_name, file.name)
        st.success("File uploaded successfully")
    except FileNotFoundError:
        st.error("The file was not found")
    except NoCredentialsError:
        st.error("Credentials not available")
        return False

    return True


def display_pdf_file(pdf_file):
        binary_data = pdf_file.getvalue()
        pdf_viewer(input=binary_data,width=700)


def initiate_rag(textract,bucket,key):
    #initialize llm and other required clients
    st.write("Files Stored in Bucket {bucket}")
    response = utils.extract_text_using_textract(textract,bucket,key)
    text = utils.extract_text(response)
#python code to convert text list to string 
    text = " ".join(text)

    #python code to split text into chunks using recrusive character text splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_text(text)
    create_network_policy = utils.create_network_policy(aoss_client, network_policy_name, vector_store_name, type='network')
    create_encryption_policy = utils.create_encryption_policy(aoss_client, encryption_policy_name, vector_store_name, type='encryption')
    create_collection_status = utils.create_collection(aoss_client, vector_store_name,type='VECTORSEARCH')
    # create access policy
    create_access_policy = utils.create_access_policy(aoss_client, access_policy_name, vector_store_name, type='data', identity=identity)
    status, collection_id, openSearch_host = utils.get_collection_status(aoss_client,vector_store_name,region)
    docs_search = utils.store_data_from_texts(docs, embeddings, openSearch_host, index_name, awsauth)
    return docs_search

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()

def display_pdf(file):
    # Opening file from file path

    st.markdown("### PDF Preview")
    base64_pdf = base64.b64encode(file.read()).decode("utf-8")

    # Embedding PDF in HTML
    pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="400" height="100%" type="application/pdf"
                        style="height:100vh; width:100%"
                    >
                    </iframe>"""

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)

def main():

    status, collection_id, openSearch_host = utils.get_collection_status(aoss_client,vector_store_name,region)
    docs_search = utils.get_opensearch_client(embeddings, openSearch_host, index_name, awsauth)

    st.title("RAG with your Images \n By Bharat Khanna")
        # Create a sidebar
    
    with st.sidebar:
        st.header("Menu")
        option = st.radio("Select an option", ["Use Existing Files", "Upload New Files"])
        show_source_documents = st.checkbox("Show Source Documents")
        if option == "Upload New Files":
            
            uploaded_files = st.file_uploader("Choose a file to upload",accept_multiple_files=True,type=['pdf','jpg'])
       

#create a web menu for uploading the file to S3
        
            display_file = st.button("Display Files:")
            if uploaded_files is not None and display_file:
                for file in uploaded_files:
        #check streamlit file type
                    if file.type == "application/pdf":
                        st.write("Displaying PDF file:")
                        with container_pdf:
                                st.write("PDF File:")
                                display_pdf_file(file)
                    elif file.type.startswith("image/"):
                        # Display image file
                            st.write("Displaying image file:")
                            st.image(file.getvalue(), use_column_width=True)
                    else:
                            st.error("Unsupported file type. Please upload a PDF or image file.")
            
            upload_files = st.button("Upload File")
            

            if upload_files:
                for file in uploaded_files:
                    upload_to_s3(file) 

            process_files = st.button("Process Files")
            if process_files:
                for file in uploaded_files:
                    st.spinner("Processing file...")
                    docs_search = initiate_rag(textract,bucket, key=file.name)


            clear_form = st.button("Clear Form")
                # Clear Button to Reset the Form
            if clear_form:
                uploaded_files = []
                st.session_state.uploaded_results = []  # Clear the uploaded_results in session state
        else:
            # qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(llm=llm, chain_type="stuff", 
            #                                                    retriever=docs_search.as_retriever(search_kwargs={'k':3}),
            #                                                    return_source_documents=True)
            
            # qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docs_search.as_retriever())         
            pass
    
        qa_prompt = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=docs_search.as_retriever(),
                # return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT},
            )

        qa_prompt_with_sources = RetrievalQAWithSourcesChain.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=docs_search.as_retriever(),
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT_WITH_SOURCES},
            )

    # Initialize chat history
    if "messages" not in st.session_state:
        reset_chat()
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
                # Get user input
    # user_input = st.text_input("You: ", key="input")
            # Process user input
    
    # Accept user input
    if prompt := st.chat_input("How can i help you ?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            sources_placeholder = st.empty()
            full_response = ""
            sources = ""
        
    # if user_input:
        if show_source_documents:
             response = qa_prompt_with_sources({"question": prompt})
             full_response = response['answer']
             sources = response['sources']
             
        else:
             response = qa_prompt({"query": prompt})

        full_response = response['result']
        message_placeholder.markdown(full_response)
        sources_placeholder.markdown(sources)

       # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        # st.session_state.conversation.append(("You: " + user_input, result["result"]))

    #     # Display conversation history
    # for human_utterance, ai_response in st.session_state.conversation:
    #     st.markdown(f"**{human_utterance}**")
    #     st.markdown(ai_response)


if __name__ == "__main__":
    main()