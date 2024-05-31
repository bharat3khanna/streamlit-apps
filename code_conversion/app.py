import streamlit as st
import boto3
import gc
import base64
from dotenv import load_dotenv, find_dotenv
from botocore.exceptions import NoCredentialsError
from streamlit_pdf_viewer import pdf_viewer
from requests_aws4auth import AWS4Auth
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain, LLMChain, SimpleSequentialChain, SequentialChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate




#load environment variables
load_dotenv(find_dotenv())

session = boto3.Session(profile_name='dev')
bedrock_client = session.client('bedrock-runtime',region_name='us-east-1')
identity = session.client('sts').get_caller_identity()['Arn']
credentials = session.get_credentials()

#initialize llm and other required clients
llm = Bedrock(client=bedrock_client, model_id="anthropic.claude-v2", model_kwargs={"max_tokens_to_sample": 1000, "temperature":0})
embeddings = BedrockEmbeddings(client=bedrock_client,model_id="amazon.titan-embed-text-v1")

template = """
You will be acting as an AI Snowflake SQL Expert named Frosty
Your goal is to give correct, executable sql query to users.
Your job is to convert the code from Microsoft SQL Server Integration Services code extracted in XML to Snowflake compatible SQL
You will be given the XML code and expected output in Snowflake compatible SQL.
The XML code will be in the following format:
<code>
...
</code>

Here are 6 critical rules for the interachtion you must abide:
<rules>

1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2.  Make sure to read the entire XML file and generate full Snowflake compatible SQL Code.
3.  Do not make any assumptions on the XML structure or the format of the XML data.
4.  The input XML is the code extracted from SSIS packages.
6.  The output should be the final converted Snowflake compatible SQL code.
7. Do not give partial query or do partial conversion. The final converted code should be a valid Snowflake compatible SQL query.
8. The final converted code should be a valid Snowflake compatible SQL query.

</rules>

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
"""
code_generation_template = """
Given the following code, convert it to Snowflake compatible SQL
{code}
"""

code_generation_prompt = ChatPromptTemplate.from_messages(
    [("system",template),("human",code_generation_template)]
)

code_generation_chain = LLMChain(llm=llm, prompt=code_generation_prompt,output_key='generated_code')
seq_chain = SequentialChain(chains=[code_generation_chain], input_variables=["code"], output_variables=["generated_code"])



st.set_page_config(page_title="SSIS To Snowflake", page_icon="⭐")
# st.header("""SSIS To Snowflake Code Conversion \n
#           By Bharat Khanna""")

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()


def main():
    
    uploaded_files = st.file_uploader("Upload XML File",accept_multiple_files=False,type=['xml'])

  

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
    st.title("""SSIS To Snowflake Code Convertor \n
          By Bharat Khanna""")
    st.write("""Hello, I am an AI assistant to help on the conversion of SSIS Packages to Snowflake Compatible SQL
             be more productive. 
             I am built on Amazon Bedrock
             To get started, please upload an XML file, and click on Process File. I will convert it to Snowflake compatible SQL.
             Press the Clear Form Button to start over.
             """)

    main()

    