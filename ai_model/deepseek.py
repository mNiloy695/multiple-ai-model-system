# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI

def call_deepseek_for_chat(model_id,api_key,user_id,base_cose,message):
    try:
       client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
       response = client.chat.completions.create(
       model="deepseek-chat",
       messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": message},
    ],
       stream=False)
       print(response.choices[0].message.content)
       return {"text":response.choices[0].message.content}
    except Exception as e:
        return {"error":"An error Occure"}