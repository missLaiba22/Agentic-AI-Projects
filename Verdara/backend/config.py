from dotenv import load_dotenv
from google import genai
from tavily import TavilyClient
import os
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set in the environment variables.")
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"   
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)