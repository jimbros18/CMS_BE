import os
import json
from dotenv import load_dotenv
from jwt.algorithms import ECAlgorithm

load_dotenv()
JWT_KEY = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

with open('jwks.json', 'r') as f:
    jwks = json.load(f)

PUBLIC_KEY = ECAlgorithm.from_jwk(jwks['keys'][0])