import os
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY)

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Hindsight Cloud
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")

# Hindsight client — lazy import to allow startup without key
def get_hindsight_client():
    try:
        from hindsight import HindsightClient
        return HindsightClient(
            base_url=HINDSIGHT_BASE_URL,
            api_key=HINDSIGHT_API_KEY
        )
    except Exception as e:
        print(f"[Hindsight] Could not initialize client: {e}")
        return None

hindsight = get_hindsight_client()
