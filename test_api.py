import requests

url = "http://127.0.0.1:8000/chat"

payload = {
    "question": "What is the weather in Bangalore?"
}

response = requests.post(
    url,
    json=payload
)

print(response.json())