from dotenv import load_dotenv
import os
from langchain.llms import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI LLM
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

llm = OpenAI(openai_api_key=api_key)
result = llm.predict("hi!")
print(result)

# from langchain. chat_models import ChatOpenAI
# chat_model = ChatOpenAI()
# chat_model.predict("hi!")



