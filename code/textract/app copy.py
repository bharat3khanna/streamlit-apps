#write a code for building a streamlit app for uploading the file to S3
import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError
from streamlit_pdf_viewer import pdf_viewer

access_key = st.secrets["AWS_ACCESS_KEY_ID"]
secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
bucket_name = st.secrets["AWS_BUCKET_NAME"]
region = st.secrets["AWS_DEFAULT_REGION"]

container_pdf, container_chat = st.columns([50, 50])

#create a function to upload the file to S3
def upload_to_s3(file):
    s3 = boto3.client('s3', aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key, region_name=region)

    try:
        s3.upload_fileobj(file, bucket_name, file.name)
        st.success("File uploaded successfully")
    except FileNotFoundError:
        st.error("The file was not found")
    except NoCredentialsError:
        st.error("Credentials not available")
        return False

    return True


def display_pdf_file(pdf_file):
        binary_data = pdf_file.getvalue()
        pdf_viewer(input=binary_data,width=700)
    




#create a web menu for uploading the file to S3
st.title("File Upload to S3")
uploaded_files = st.file_uploader("Choose a file to upload",accept_multiple_files=True,type=['pdf','jpg'])
display_file = st.button("Display Files:")
upload_files = st.button("Upload File")


if uploaded_files is not None and display_file is not None:
    for file in uploaded_files:
#check streamlit file type 
        st.write(file.type)
        if file.type == "application/pdf":
            st.success("PDF file uploaded successfully!")
            st.write("Displaying PDF file:")
            with container_pdf:
                st.write("PDF File:")
                display_pdf_file(file)
        elif file.type.startswith("image/"):
        # Display image file
            st.success("Image file uploaded successfully!")
            st.write("Displaying image file:")
            st.image(file.getvalue(), use_column_width=True)
        else:
            st.error("Unsupported file type. Please upload a PDF or image file.")
    # for file in uploaded_file:
    #     if file:
    #         file_contents = file.read()
    #         st.write(f'File:{file.name}')
    #         st.code(file_contents)

if upload_files:
    for file in uploaded_files:
        upload_to_s3(file)

# Clear Button to Reset the Form
if st.button("Clear Form"):
    bucket_name = ""
    uploaded_files = []
    st.session_state.uploaded_results = []  # Clear the uploaded_results in session state

def main():

        # Create a sidebar
    with st.sidebar:
        st.header("Options")
        option = st.radio("Select an option", ["Upload Files", "View Uploaded Files"])


if __name__ == "__main__":
    main()