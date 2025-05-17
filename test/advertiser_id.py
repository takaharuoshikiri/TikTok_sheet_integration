import requests

# 自分のアクセストークンをここに入力
ACCESS_TOKEN = '9552d08e79c2028f31329663cf6aa2ed320bd10b'

# TikTok APIのエンドポイント
url = 'https://business-api.tiktok.com/open_api/v1.2/oauth2/advertiser/get/'

# ヘッダーにアクセストークンを設定
headers = {
    'Access-Token': ACCESS_TOKEN
}

# GETリクエストを送信
response = requests.get(url, headers=headers)

# レスポンスを表示
if response.status_code == 200:
    data = response.json()
    advertisers = data.get("data", {}).get("list", [])
    
    if advertisers:
        for adv in advertisers:
            print(f"Advertiser Name: {adv.get('advertiser_name')}")
            print(f"Advertiser ID: {adv.get('advertiser_id')}")
            print('-------------------------')
    else:
        print("Advertiser ID が見つかりませんでした。")
else:
    print(f"エラー: ステータスコード {response.status_code}")
    print(response.text)
