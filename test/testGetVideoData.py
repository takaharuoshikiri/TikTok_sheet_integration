import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from refresh_token import refresh_token
from videoFieldsName import VIDEO_FIELDS
from date_utils import get_date_range
from outputToJson import outputToJson



"""
TikTok Business APIを使用してビジネスアカウント情報を取得する
API Doc: https://business-api.tiktok.com/portal/docs?id=1739940603393026 (推定されるドキュメント)
※注意: 上記ドキュメントURLは/business/get/に関する直接的なものではない可能性があります。
       正確なドキュメントはTikTok Business API Portalで確認してください。
"""
#4月20日：毎回の実行の前にrefresh_token.pyを用いてアクセストークンとリフレッシュトークンを更新する仕組みを実装しておかないとダメぽい
#4/24日付の取得をdatetimeを利用した処理に変更、todayはどの関数でも値が必ず一緒なのでグローバルで定義しておいて問題ない
# --- curlコマンドから抽出した設定 ---

# APIエンドポイント (curlコマンドのURLから)
# 注意: クエリパラメータは `params` 引数で渡すため、ベースURLのみを記述します
url = "https://business-api.tiktok.com/open_api/v1.3/business/video/list/"

access_token = refresh_token()

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
business_id = os.getenv("TIKTOK_BUSINESS_ID") # 実際のBusiness IDに置き換えてください
fields_list = VIDEO_FIELDS
start_date, end_date = get_date_range(3,2)

params = {
    "business_id": business_id,
    "fields": json.dumps(fields_list), # リストをJSON文字列に変換
    "start_date": start_date,
    "end_date": end_date
}

def getVideoAPI():

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
            post_date_str = end_date
            response_data['post_date'] = post_date_str
            print("Response JSON:")
            # JSONデータを整形して表示
            print(json.dumps(response_data, indent=4, ensure_ascii=False))

            outputToJson(response_data)

            return response_data
    
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
        return None
    

if __name__ == "__main__":
    getVideoAPI()