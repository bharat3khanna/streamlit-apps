from openai import OpenAI
import re
import streamlit as st
from daas_prompts import get_system_prompt
import pandas as pd
import plotly.express as px


# Function to create a bar chart
# def create_bar_chart(df):
#     # Get column names and values
#     columns = df.columns
#     values = df.iloc[0].values

#     # Create a DataFrame for the chart
#     chart_data = pd.DataFrame({'Column': columns, 'Value': values})

#     # Create a bar chart using Altair
#     chart = alt.Chart(chart_data).mark_bar().encode(
#         x='Column',
#         y='Value'
#     ).properties(
#         width=alt.Step(80)
#     )

#     return chart

def create_plotly_bar_chart(df,x,y):
    #if len(df.columns) == 2:
    return px.bar(df,x=x,y=y)
    #return st.bar_chart(df, x=x,y=y,color='grey', use_container_width=True)
    #else:
    #st.write('Insufficent Number of Columns for Bar Chart')
            

def create_plotly_line_chart(df,x,y):
    return px.line(df,x=x,y=y)
    #return st.line_chart(df,x=df.columns[0],y=df.columns[1],color='grey',use_container_width=True)

def create_plotly_pie_chart(df,x,y):
    return px.pie(df,values=x,names=y)

#Program Starts Here

st.title("Welcome to Casino.AI")

# Initialize the chat messages history
client = OpenAI(api_key=st.secrets.OPEN_API_KEY)
if "messages" not in st.session_state:
    # system prompt includes table information, rules, and prompts the LLM to produce
    # a welcome message to the user.
    st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]

# Prompt for user input and save
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

# display the existing chat messages
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "results" in message:
            st.dataframe(message["results"])

# If last message is not from assistant, we need to generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
   # if st.session_state.messages.count(1)>1 :
        with st.spinner('Processing!! Hang on Tight !!'):
            
            with st.chat_message("assistant"):
                response = ""
                resp_container = st.empty()
                for delta in client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True,
                ):
                    response += (delta.choices[0].delta.content or "")
                    resp_container.markdown(response)

            message = {'role':'assistant','content':response}
st.session_state.messages.append(message)


#Parse the response
sql_match = re.search(r"```sql\n(.*)\n```", response,re.DOTALL)
if sql_match:
    sql = sql_match.group(1)
    conn = st.connection('snowflake')
    data = conn.query(sql)
    message['results'] = data
    #df = st.dataframe(message['results'])

    #st.dataframe(df)
    #if not df.empty and df is not None:
    df = pd.DataFrame(data)
    st.dataframe(df)
    #st.write(df)
    st.session_state.messages.append(message)      
    #charts = st.button('Show Charts')
    #st.expander('Show Charts',expanded=False)
        
    st.subheader('Charts')
    #if charts:
    x_axis_label = st.selectbox("Select X-axis:", df.columns.values.tolist(), index=0)
    y_axis_label = st.selectbox("Select Y-axis:", df.columns[1:].values.tolist(), index=0)
    tabs = st.tabs(['Bar Chart','Line Chart','Pie Chart'])
        #st.subheader('Bar Chart')
        #chart = create_bar_chart(df)
        #st.altair_chart(chart, use_container_width=True)
        
    with tabs[0]:
            #px.bar(df,x=df.columns[0],y=df.columns[1])
            #st.bar_chart(df,x=df.columns[0],y=df.columns[1])
        fig1 = create_plotly_bar_chart(df=df,x=x_axis_label,y=y_axis_label)
        st.plotly_chart(fig1,use_container_width=True)
    with tabs[1]:
        fig2 = create_plotly_line_chart(df=df,x=x_axis_label,y=y_axis_label)
        st.plotly_chart(fig2,use_container_width=True)
    with tabs[2]:
        fig3 = create_plotly_pie_chart(df=df,x=x_axis_label,y=y_axis_label)
        st.plotly_chart(fig3,use_container_width=True)
