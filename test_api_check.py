import requests
import json

try:
    # Correct key is 'playerName'
    payload = {"playerName": "CristianoRonaldo"}
    headers = {"Content-Type": "application/json"}
    
    res = requests.post("http://127.0.0.1:5000/api/analyze/player", json=payload, headers=headers)
    
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print("Analysis Keys:", data.get("analysis", {}).keys())
        print("Data Sources:", data.get("analysis", {}).get("dataSources"))
        print("Highlight:", data.get("analysis", {}).get("careerHighlight"))
        print("Team Fit Count:", len(data.get("recommendations", {}).get("teamFit", [])))
        if data.get("recommendations", {}).get("teamFit"):
            print("First Fit:", data["recommendations"]["teamFit"][0])
    else:
        print(res.text)

except Exception as e:
    print(f"Error: {e}")
