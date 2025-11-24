# from openai import OpenAI

# api_key = ""  # keep this private

# client = OpenAI(api_key=api_key)

# try:
#     models = client.models.list()
#     print("Models your key can see:")
#     for m in models.data:
#         print("-", m.id)
# except Exception as e:
#     print("Error:", e)


from google import genai
from google.genai import types

# Your API key
# API_KEY = ""

# # Initialize client
# client = genai.Client(
#     api_key=API_KEY,
#     # http_options=types.HttpOptions(api_version="v1")  # always use v1
# )

# # Fetch all models
# models = client.models.list()

# # Print details
# for m in models:
#     print("Model Name:", m.name)
#     print("Supported Methods:", getattr(m, "supported_generation_methods", []))
#     print("Input Modalities:", getattr(m, "input_modalities", []))
#     print("Output Modalities:", getattr(m, "output_modalities", []))
#     print("-" * 50)

# import requests

# WAVESPEED_API_KEY = ""

# API_KEY = WAVESPEED_API_KEY

# url = "https://api.wavespeed.ai/api/v3/models"

# response = requests.get(
#     url,
#     headers={"Authorization": f"Bearer {API_KEY}"}
# )

# print("STATUS:", response.status_code)
# print("RAW:", response.text)

# # Only try to parse JSON if it's successful
# if response.status_code == 200:
#     print("JSON:", response.json())
# else:
#     print("Could not parse JSON because status is not 200.")

#see all model of gemini by api call
import requests

API_KEY = ""
url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

response = requests.get(url)

print("STATUS:", response.status_code)
print("RAW:", response.text)

if response.status_code == 200:
    print("JSON:", response.json())
else:
    print("Could not parse JSON because status is not 200.")
