import requests
import json

"""
/oauth/トークン/
https://business-api.tiktok.com/portal/docs?id=1739965703387137
"""

# APIエンドポイント
url = "https://business-api.tiktok.com/open_api/v1.3/oauth/token/"

# ヘッダー
headers = {
    "Content-Type": "application/json"
}

# データペイロード
payload = {
    "client_id": "7367211510419947537",
    "client_secret": "0929b845536ee82c14855c511ee6ed1b539ebb3f",
    "code": "c4f464c09377473538d93b4c87fff90d3854d300",
    "grant_type": "authorization_code"
}

# リクエストの送信
response = requests.post(url, headers=headers, data=json.dumps(payload))

# レスポンスの確認
if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)