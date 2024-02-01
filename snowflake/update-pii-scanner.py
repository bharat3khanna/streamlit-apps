import snowflake.connector as con 
from snowflake.snowpark import Session
import streamlit as st
import utils
import json
import pandas as pd
import time

if 'snowflake-connection' not in st.session_state:
    #Connect to Snowflake
    with open('creds.json') as f:
        connection_params = json.load(f)
    st.session_state.snowflake_connection = Session.builder.configs(connection_params).create()
    session = st.session_state.snowflake_connection
else:
    session = st.session_state.snowflake_connection

st.set_page_config(layout="centered", page_title="Data Editor", page_icon="🧮")
st.title("Snowflake Table Editor ❄️")
st.caption("This is a demo of the `st.experimental_data_editor`.")

def get_dataset(table):
    # load messages df
    df = session.table(table)

    return df

dataset = get_dataset('SOURCE_DATA.INPUT_DATA.CUSTOMER')

with st.form("data_editor_form"):
    st.caption("Edit the dataframe below")
    edited = st.experimental_data_editor(dataset, use_container_width=True, num_rows="dynamic")
    submit_button = st.form_submit_button("Submit")

if submit_button:
    try:
        #Note the quote_identifiers argument for case insensitivity
        session.write_pandas(edited, 'CUSTOMER',database='SOURCE_DATA',schema='INPUT_DATA',overwrite=True, quote_identifiers=False)
        st.success("Table updated")
        time.sleep(5)
    except:
        st.warning("Error updating table")
    #display success message for 5 seconds and update the table to reflect what is in Snowflake
    st.experimental_rerun()


