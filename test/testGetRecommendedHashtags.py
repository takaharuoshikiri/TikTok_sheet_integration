import requests
import json

"""
TikTok Business APIを使用してビジネスアカウント情報を取得する
API Doc: https://business-api.tiktok.com/portal/docs?id=1739940603393026 (推定されるドキュメント)
※注意: 上記ドキュメントURLは/business/get/に関する直接的なものではない可能性があります。
       正確なドキュメントはTikTok Business API Portalで確認してください。
"""
#4月17日成功！！（フィールドのいじり方はこれから）
# --- curlコマンドから抽出した設定 ---

# APIエンドポイント (curlコマンドのURLから)
# 注意: クエリパラメータは `params` 引数で渡すため、ベースURLのみを記述します
url = "https://business-api.tiktok.com/open_api/v1.3/business/hashtag/suggestion/"

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
#start_dateは今日の日付から60日以前だとエラーが出る。
business_id = "-000GlCTHa4_dkqLBG4sczTYmZgmNGSRXF3j"
keyword = "ポケモンカード151"
language = "ja-JP"
#fields_list = ["item_id","create_time","thumbnail_url","share_url","embed_url","caption","video_views","likes","comments","shares","reach","video_duration","full_video_watched_rate","total_time_watched","average_time_watched","impression_sources","audience_countries","new_followers","profile_views","website_clicks"]
#keywordsは一つしか無理っぽい

params = {
    "business_id": business_id,
    "keyword": keyword,
    "language": language,
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