from openai import OpenAI
import streamlit as st
from PIL import Image

img = Image.open("./data/Chikku.jpg")

st.image(img)
st.title('Welcome To Chikkupedia')
st.balloons()

client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

#Initialize the chat history
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{'role':'assistant','content':'Ask me anything?'}]

#prompt user for messages
if prompt := st.chat_input():
    st.session_state.messages.append({'role':'user','content':prompt})

# Display all messages based on history
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.write(message['content'])

assistant_response_message = 'Bas !! Hor Kuch Puchna ??'

if st.session_state.messages[-1]['role'] != 'assistant':
    #Call LLM
    with st.chat_message('assistant'):
        with st.spinner('Rukk Dasda Tenu'):
            r = client.chat.completions.create(
                messages=[{'role':m['role'],'content':m['content']} for m in st.session_state.messages],
                model='gpt-3.5-turbo'
            )

            response = r.choices[0].message.content
            st.write(response)
        st.write(assistant_response_message)
    message = {'role':'assistant','content':response}
    st.session_state.messages.append(message)
    assistant_response_message = 'Bas !! Hor Kuch Puchna ??'
    message = {'role':'assistant','content':assistant_response_message}
    st.session_state.messages.append(message)
    
