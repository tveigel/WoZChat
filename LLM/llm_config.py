
from dotenv import load_dotenv
import os
import getpass

from langchain_openai import AzureChatOpenAI


# Load environment variables from .env file
load_dotenv()




API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")


llm = AzureChatOpenAI(
    azure_deployment="gpt-v4.1-w1000000",
    api_version=API_VERSION,       
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    temperature=0.1,
    max_tokens=4096,
    timeout=60,
)




