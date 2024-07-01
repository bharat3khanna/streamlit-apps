import streamlit as st
import boto3
import gc
import base64
from dotenv import load_dotenv, find_dotenv
# from botocore.exceptions import NoCredentialsError
# from streamlit_pdf_viewer import pdf_viewer
# from requests_aws4auth import AWS4Auth
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain, LLMChain, SimpleSequentialChain, SequentialChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate

from botocore.config import Config
# Create a custom config with increased read timeout
config = Config(
    read_timeout=1000  # Set the read timeout value in seconds (e.g., 1000 seconds = 16.67 minutes)
)

#load environment variables
load_dotenv(find_dotenv())

# access_key = st.secrets["AWS_ACCESS_KEY_ID"]
# secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
# # bucket_name = st.secrets["AWS_BUCKET_NAME"]
# region = st.secrets["AWS_DEFAULT_REGION"]
# container_pdf, container_chat = st.columns([50, 50])

# session = boto3.Session(aws_access_key_id=access_key,
                    #   aws_secret_access_key=secret_key, region_name=region)

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1',config=config)
identity = session.client('sts').get_caller_identity()['Arn']
credentials = session.get_credentials()

#initialize llm and other required clients
llm = Bedrock(client=bedrock_client, model_id="anthropic.claude-v2", model_kwargs={"max_tokens_to_sample": 50000, "temperature":0})
embeddings = BedrockEmbeddings(client=bedrock_client,model_id="amazon.titan-embed-text-v1")

template = """
You will be acting as an AI Redshift SQL Expert named Frosty
Your goal is to give correct, executable sql query to users.
Your job is to convert the code from Oracle code extracted in SQL to Redshift compatible SQL
You will be given the Oracle code and expected output in Redshift compatible SQL.
The XML code will be in the following format:
<code>
...
</code>

Here are 6 critical rules for the interaction you must abide:
<rules>

1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2.  Make sure to read the entire Oracle code file and generate full Redshift compatible SQL Code.
3.  Do not make any assumptions on the Oracle code structure or the format of the Oracle code data.
4.  The input file is the code extracted from Oracle .
6.  The output should be the final converted Redshift compatible SQL code.
7.  Do not give partial query or do partial conversion. The final converted code should be a valid Redshift compatible SQL query.
8. The final converted code should be a valid Redshift compatible SQL query.

</rules>

Now to get started, please briefly introduce yourself
"""
code_generation_template = """
Given the following code, convert it to Redshift compatible SQL
{code}
"""

code_generation_prompt = ChatPromptTemplate.from_messages(
    [("system",template),("human",code_generation_template)]
)

code_generation_chain = LLMChain(llm=llm, prompt=code_generation_prompt,output_key='generated_code')
seq_chain = SequentialChain(chains=[code_generation_chain], input_variables=["code"], output_variables=["generated_code"])

# st.set_option('theme.primaryColor', '#0072C6')
# st.set_option('theme.backgroundColor', '#1E1E1E')
# st.set_option('theme.textColor', '#FFFFFF')
# st.set_option('theme.font', 'sans-serif')

st.set_page_config(page_title="Oracle to Redshift", page_icon="⭐")
# st.header("""SSIS To Redshift Code Conversion \n
#           By Bharat Khanna""")

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()


def main():
    
    uploaded_files = st.file_uploader("Upload  File",accept_multiple_files=False,type=['sql'])

  

    clear_form = st.button("Clear Form")
                # Clear Button to Reset the Form
    if clear_form:
                uploaded_files = []
                st.session_state.uploaded_results = []
                st.session_state.clear()


    # Initialize the chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

     # Add the user's file content to the chat history
    # st.session_state.chat_history.append({"role": "user", "content": file_content})
    process_file = st.button("Process File")

    if process_file and uploaded_files is not None:
        with st.spinner("Processing File..."):
            # if uploaded_files is not None:
            # for file in uploaded_files:
                    # if file.type == "application/xml":
                    #     st.write("XML File:")
                    #     st.write(file.name)
                    #     st.write(file.getvalue())
            file_content = uploaded_files.read().decode("utf-8")
                    # else:
                    #     st.error("Unsupported file type. Please upload a XML file.")
            response = seq_chain.run(code=file_content)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # response = seq_chain.run(code=file_content)
    
    # # Add the LLM's response to the chat history
    # st.session_state.chat_history.append({"role": "assistant", "content": response})


    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if __name__ == "__main__":
    # st.set_option('theme.primaryColor', '#0072C6')
    # st.set_option('theme.backgroundColor', '#1E1E1E')
    # st.set_option('theme.textColor', '#FFFFFF')
    # st.set_option('theme.font', 'sans-serif')
    st.write("""Hello, I am an AI assistant to help on the conversion of Oracle Code  to Redshift Compatible SQL
             be more productive. 
             I am built on Amazon Bedrock
             To get started, please upload an Oracle Code file, and click on Process File. I will convert it to Redshift compatible SQL.
             Press the Clear Form Button to start over.
             """)

    main()

    