import requests

headers = {
    "Authorization": "Bearer <access-token>"
}

re = requests.get("http://localhost:8000/monitor/127.0.0.1", headers=headers)

print(re)
print()
print(re.json)
