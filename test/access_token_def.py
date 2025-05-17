import requests

url = "https://business-api.tiktok.com/open_api/v1.3/tt_user/oauth2/token/"

headers = {
    "Content-Type": "application/json"
}

payload = {
    "app_id": "7480734449341038609",  # あなたのapp_id
    "secret": "01fe5c05bf14a9cb67b1d2e4cbc79b8d73e555bc",     # TikTok Businessで発行されたsecret
    "auth_code": "c4363ca4eca895394f4d341a1536f5715978f80b"
}
response = requests.post(url, headers=headers, json=payload)

print(response.json())


