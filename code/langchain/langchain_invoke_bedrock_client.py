import boto3
from langchain.llms.bedrock import Bedrock


session = boto3.Session(profile_name='dev')
bedrock_runtime = session.client('bedrock-runtime',region_name='us-east-1')

inference_modifier = {
    "max_tokens_to_sample": 4096,
    "temperature": 0.5,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}


textgen_llm = Bedrock(
    model_id="anthropic.claude-v2",
    client=bedrock_runtime,
    model_kwargs=inference_modifier,
)


response = textgen_llm("""

Human: Write an email from Bob, Customer Service Manager, 
to the customer "Bharat Khanna" that provided negative feedback on the service 
provided by our customer support engineer.

Assistant:""")

print(response)
