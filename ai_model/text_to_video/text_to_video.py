import os
import requests
import json
import time
#text_to_video_generation(model_id,prompt,api_key,duration,height,width,seed=-1)

def text_to_video_generation(model_id,prompt,api_key,duration,height,width,seed=-1):
    API_KEY = api_key
    url = f"https://api.wavespeed.ai/api/v3/{model_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "duration": duration,
        "enable_prompt_expansion": False,
        "prompt": prompt,
        "seed": seed,
        "size": "1280*720"
    }

    begin = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result = response.json()["data"]
        request_id = result["id"]
        print(f"Task submitted successfully. Request ID: {request_id}")
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return

    url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    # Poll for results
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()["data"]
            status = result["status"]

            if status == "completed":
                end = time.time()
                print(f"Task completed in {end - begin} seconds.")
                url = result["outputs"][0]
                print(f"Task completed. URL: {url}")
                break
            elif status == "failed":
                print(f"Task failed: {result.get('error')}")
                break
            else:
                print(f"Task still processing. Status: {status}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

        time.sleep(0.5)
    return url

