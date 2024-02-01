import snowflake.connector as con 
import streamlit as st
import utils
import json


st.title('Connecting to Snowflake')

with st.sidebar:
    session = utils.getRemoteSession()
    if session is not None:
        tablename = st.text_input('Enter the table name you want to query')


#conn = st.connection("snowflake")
#query = f'Select * from {tablename}'
#df = conn.query(query,ttl=360,show_spinner="Running `snowflake.query(query)`")
#st.dataframe(df)
#st.write('Querying {query}')
