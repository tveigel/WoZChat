import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()






llm = AzureChatOpenAI(
    azure_deployment="my‑gpt‑4o‑deployment",
    api_version="2025-03-01-preview",
    model_version="0513",          # optional – tags the response metadata
    temperature=0.3,
    max_tokens=2048,
    timeout=60,
)
