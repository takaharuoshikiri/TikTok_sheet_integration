import requests
import json

"""
アクセストークンを介して承認されたTikTokアカウントの権限スコープを取得する
https://business-api.tiktok.com/portal/docs?id=1765927978092545
"""

# APIエンドポイント
url = "https://business-api.tiktok.com/open_api/v1.3/tt_user/token_info/get/"

# ヘッダー
headers = {
    "Content-Type": "application/json"
}

# データペイロード
payload = {
    "app_id": "7480734449341038609",
    "access_token": "769b7d5e7a4dc8c31d259e395c1437a721184f95"
}

# リクエストの送信
response = requests.get(url, headers=headers, data=json.dumps(payload))

# レスポンスの確認
if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)