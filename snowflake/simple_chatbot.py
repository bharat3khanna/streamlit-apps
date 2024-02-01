from openai import OpenAI
import streamlit as st
from PIL import Image

img = Image.open("https://streamlit-bkhanna.s3.us-east-1.amazonaws.com/Chikku.jpg?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEIj%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJIMEYCIQCTGVO1aIYmV2X1Dc%2BQ2quRJvpmZ1E190odO%2BsTNLKUzwIhAJEFR2ITmKxal17RvYUN%2Bj23u2jCRjU4hPOMh%2FgmSkh1KvsCCFEQBBoMNTkwMzA1OTgwMzA4Igwh6eBGRZnwGaHxHOMq2AKainoIaNx1Hm4EABL42j%2F9iaQzzElfGVuo0kVyo8l83OZyeWvDiW1kk%2BFaGASE%2Bl2crpS%2FUk94%2F4DYmqoe%2BCsaLM8CHFup4QzWuT8Y0GgUBRZ0mgmLlciD50GeL1EYehscCngXu7yie6kQ9Bu8%2Blxfp50RGQQVnsrRUGmLjQObIq9lL31v10PphwO4NBoNmnPN%2B6Cg3FuEN3sZNow%2Ffn9Qk5AN6by5GUqFuBs12t2D0tPYsdIW0HezPufrD8R42BK8kApydTvggLsnu8kqOyoRuRESWCuBAlKGUepCOqpbaAfMBiX%2BykMRSVrQYcCplosu5mdyd14InTCeL%2BuaKXdVH9OuPSVCETG%2B3Ny6vfVB5XBnS73M%2FI1QM0qRyj6ELcvLMc69BZMxcz0J7tfEnqjDjHYfaLoXy%2BvE1Hxbbnb0zX3BLxwTX7Dr1XijO035%2FO52WXt2NByRuzD92vCtBjqyAsHAceNkzzQ%2FFjnpib6XD6keLOWZwVPDOTFZ49nn5d3DN8FECs4rWCssN%2Fjz9IXYaumvFcYDG2zl7nwuV6367GRfELVmwR51WkgrjQV9HvRaQaWn3VaJ3R3HaHLWS4RpFTX6JlaxI8mdZkJVsbZC9dEiz5vIFLOuJKaUXVmnm0LddmzPGwAwX0%2B6s235ro3TPjdpqedgvtO%2F7g78V5J7%2FfdUtrcQMzC3Ac9XRZrJmPPSJxMVvrvlFGry8Ie8aOhIXl9Yqp50tzpvsoTGwclp%2FpfIhIZRkMFyWybth5kZQ2lmFESRczmrpdMWD5snxFznpxU1%2Bhm7%2Fj72Xni2M5IAp2jVMzJ576UYaidBOXO%2BfMIRsCUaUFMNu5weVC2pNBe6Z%2F5a5DiVxpk%2F%2Fzl7AZ8hNswCxg%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240201T235605Z&X-Amz-SignedHeaders=host&X-Amz-Expires=43200&X-Amz-Credential=ASIAYS4H2N6KCLXCKGHS%2F20240201%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=fa7f2dd7c4bd52b08d23a31aec326c10001645eec8cfcd5a97afa1b83f49ed59")

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
    
