import requests

api_key = "YOUR_LEONARDO_API_KEY"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get("https://cloud.leonardo.ai/api/rest/v1/models", headers=headers)
models = response.json().get("models", [])

# Create a mapping: Likely API Name -> Model ID
model_map = {}
for m in models:
    model_map[m["name"]] = m["id"]

# Example output
print(model_map)
