import requests
import json

"""
TikTok Business APIを使用してビジネスアカウント情報を取得する
API Doc: https://business-api.tiktok.com/portal/docs?id=1739940603393026 (推定されるドキュメント)
※注意: 上記ドキュメントURLは/business/get/に関する直接的なものではない可能性があります。
       正確なドキュメントはTikTok Business API Portalで確認してください。
"""

# --- curlコマンドから抽出した設定 ---

# APIエンドポイント (curlコマンドのURLから)
# 注意: クエリパラメータは `params` 引数で渡すため、ベースURLのみを記述します
url = "https://business-api.tiktok.com/open_api/v1.3/business/benchmark/"

# アクセストークン (curlコマンドのヘッダーから)
# 重要: このトークンはサンプルです。実際の有効なトークンに置き換えてください。
access_token = "act.CT1xYxEuLnB05mGXjKJfpSGOo3Wa1WIDm2a3TFo74awXFJ5M1XmSWXkzVfL3!5342.va"

# ヘッダー (curlコマンドのヘッダーから)
headers = {
    "Access-Token": access_token
    # GETリクエストの場合、通常 Content-Type は不要ですが、
    # APIによっては要求される場合もあります。
    # "Content-Type": "application/json"
}

# クエリパラメータ (curlコマンドのURLの ? 以降から)
# fieldsパラメータはJSON配列の文字列として渡す必要があるため、json.dumpsを使用します。
business_id = "-000GlCTHa4_dkqLBG4sczTYmZgmNGSRXF3j" # 実際のBusiness IDに置き換えてください
business_category = "HOME_FURNITURE_AND_APPLIANCES"

params = {
    "business_id": business_id,
    "business_category":business_category,
}

# --- APIリクエストの実行 ---
print(f"Requesting URL: {url}")
print(f"Headers: {headers}")
print(f"Params: {params}")

try:
    # GETリクエストを実行
    response = requests.get(url, headers=headers, params=params)

    # レスポンスステータスコードを確認
    response.raise_for_status()  # ステータスコードが 2xx でない場合に例外を発生させる

    # レスポンス内容 (JSON形式と仮定) を表示
    print("\nResponse Status Code:", response.status_code)
    try:
        response_data = response.json()
        print("Response JSON:")
        # JSONデータを整形して表示
        print(json.dumps(response_data, indent=4, ensure_ascii=False))
    except json.JSONDecodeError:
        print("Response is not in JSON format:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"\nError during requests to {url}: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response text: {e.response.text}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")