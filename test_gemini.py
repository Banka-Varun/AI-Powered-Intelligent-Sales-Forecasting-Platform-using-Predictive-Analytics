print("1. Script started", flush=True)

import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

print("2. Packages imported", flush=True)

env_path = Path(__file__).with_name(".env")
load_dotenv(env_path, override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise SystemExit(f"Missing GEMINI_API_KEY in: {env_path}")

print("3. API key loaded", flush=True)

try:
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60000,
            retry_options=types.HttpRetryOptions(attempts=1)
        )
    )

    print("4. Sending request to Gemini...", flush=True)

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Reply with only: Connection successful"
    )

    print("5. Response received:", flush=True)
    print(response.text or "Response contained no text.", flush=True)

except KeyboardInterrupt:
    print("\nTest stopped by you.", flush=True)

except Exception as error:
    print(f"\n{type(error).__name__}: {error}", flush=True)