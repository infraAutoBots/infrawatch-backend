import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4Mjg4ODc2fQ.yIT1WYVrPVTeuBYjyBb-vgf3dTI4sIu_T2JI1Hw5z3M"
}

re = requests.get("http://localhost:8000/monitor/127.0.0.1", headers=headers)

print(re)
print()
print(re.json)
