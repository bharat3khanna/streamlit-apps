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

def getQueryResult(q):
    df = session.sql(query=q)
    return session.create_dataframe(df.collect())

# query = "Select config_id, db_name, schema_name, table_name, column_name, privacy_category, \
# semantic_category, user_defined_tag, tag_allowed_values, masking_required \
# from daas_dev.daas_security.data_classification_config \
# where masking_required='P' \
# order by config_id"

query = "Select * from source_data.input_data.customer where id = 1"

dataset = getQueryResult(query)



with st.form("data_editor_form"):
    st.caption("Edit the dataframe below")
    edited = st.experimental_data_editor(dataset, use_container_width=True, num_rows="dynamic")
    submit_button = st.form_submit_button("Save Data")

if submit_button:
    