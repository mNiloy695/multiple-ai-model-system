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
API_KEY = ""

# Initialize client
client = genai.Client(
    api_key=API_KEY,
    # http_options=types.HttpOptions(api_version="v1")  # always use v1
)

# Fetch all models
models = client.models.list()

# Print details
for m in models:
    print("Model Name:", m.name)
    print("Supported Methods:", getattr(m, "supported_generation_methods", []))
    print("Input Modalities:", getattr(m, "input_modalities", []))
    print("Output Modalities:", getattr(m, "output_modalities", []))
    print("-" * 50)
