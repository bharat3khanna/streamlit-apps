import streamlit as st
from snowflake.snowpark import Session

#@st.cache_resource(show_spinner='Connecting to Snowflake',max_entries=3)
def getSession(account,user,_password):
    try:
        return Session.builder.configs({
            'account':account,
            'user':user,
            'password':_password
        })

    except:
        return None

def getRemoteSession():
    session = None
    with st.form('Snowflake-Connection-Form'):
        account = st.text_input('Account #')
        user = st.text_input('User')
        password = st.text_input('Password',type='password')
        st.form_submit_button('Connect To Snowflake')
        if len(account) > 0 and len(user) > 0 and len(password) > 0:
            session = getSession(account,user,password)
            if session is None:
                st.error('Error Connecting To Snowflake. Please check your user name and password')
            else:
                st.success('Successfully Connected to Snowflake')
    return session        


