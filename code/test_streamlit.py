#write a code for building a streamlit app for uploading the file to S3
import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError

access_key = st.secrets["aws_access_key"]
st.write(access_key)
