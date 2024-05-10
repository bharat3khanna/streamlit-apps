import streamlit as st
import os
from langchain.llms import OpenAI, Bedrock
from langchain.chains import ConversationChain, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

st.set_page_config(page_title="Context aware chatbot", page_icon="⭐")
st.header('Context aware chatbot')
st.write('Enhancing Chatbot Interactions through Context Awareness')

def create_chain(document_store):
    #load llm model and embeddings
    llm = HuggingFaceHub(repo_id='google/flan-t5-large',
                     model_kwargs={"temperature":0.1, "max_length":512})
    
    #create memory object
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    #create conversation system with source document retrieval and our prompt
    qa_chain = ConversationalRetrievalChain.from_llm(llm=llm,
                                                     retriever=document_store.as_retriever(search_type="mmr",
                                                                                           search_kwargs={"k":5,
                                                                                                          "fetch_k":10}),
                                                     memory=memory)
    return qa_chain


#image for bot
bot_template = "<img src='https://upload.wikimedia.org/wikipedia/en/e/e6/WALL-E_%28character%29.jpg' width=35 height=35 style='border:1px solid black; border-radius: 50%; object-fit: cover;'>"

#image for user
user_template = "<img src='https://static.tvtropes.org/pmwiki/pub/images/linguinei_feom_ratatsaoiulle_9937.png' width=35 height=35 style='border:1px solid black; border-radius: 50%; object-fit: cover;'>"

def process_question(input_query):
    #send user query to qa chain saved in session state memory
    response = st.session_state.conversation({'question': input_query, 'chat_history': st.session_state.chat_history})

    #save chat history to session state memory
    st.session_state.chat_history = response['chat_history']
    
    #iterate through chat history in reverse order
    for question_num, message in enumerate(st.session_state.chat_history[::-1]):
        #append answers to list so that user is above assistant with the most recent text
        if question_num % 2 != 0:
            st.write(f"<div style='text-align: left;'>{user_template}&emsp;<font size='2'><u>User:</u>&nbsp;&nbsp;{message.content}</font></div><br>",
                     unsafe_allow_html=True)
        else:
            st.write(f"<div style='text-align: left;'>{bot_template}&emsp;<font size='2'><u>Bot:</u>&nbsp;&nbsp;{message.content}</font></div><br>",
                     unsafe_allow_html=True)

#start streamlit instance
st.title('PDF ChatBot')

#initialize chat history and conversation in session memory
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = None
    
#get user query
user_question = st.text_input("What would you like to ask about your pdf?")

#process user question in streamlit session state
if user_question:
    process_question(user_question)

#when button pressed
if st.button('Read.'):
    with st.spinner('Reading'):
        os.environ['HUGGINGFACEHUB_API_TOKEN'] = HUGGINGFACEHUB_API_TOKEN
            #create document store for pdf
        document_store = create_document_store(uploaded_file)

            #create chain for model to process conversation
        st.session_state.conversation = create_chain(document_store)
        st.write('Finished reading.')
