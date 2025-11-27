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
# import requests

# API_KEY = ""
# url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

# response = requests.get(url)

# print("STATUS:", response.status_code)
# print("RAW:", response.text)

# if response.status_code == 200:
#     print("JSON:", response.json())
# else:
#     print("Could not parse JSON because status is not 200.")


# fla ai api
# "74eb235b-2f39-426e-a526-26a2a52b1695:e430c6166fd9fe24479512fe9f6d8d87"



# import fal_client
# import os
# os.environ["FAL_KEY"] = "74eb235b-2f39-426e-a526-26a2a52b1695:e430c6166fd9fe24479512fe9f6d8d87"
# def on_queue_update(update):
#     if isinstance(update, fal_client.InProgress):
#         for log in update.logs:
#            print(log["message"])

# try:
#     result = fal_client.subscribe(
#     "fal-ai/flux/dev",
#     arguments={
#         "prompt": "a cat",
#         "seed": 6252023,
#         "image_size": "landscape_4_3",
#         "num_images": 4
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
#     headers={"X-Custom-Header": "value"},  # Optional: custom headers
#     )
#     print(result)
# except Exception as e:
#     print("Error during image generation:", e)






