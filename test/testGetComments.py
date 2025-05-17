import requests
import json
import os
from dotenv import load_dotenv
import datetime

from refresh_token import refresh_token

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
url = "https://business-api.tiktok.com/open_api/v1.3/business/comment/list/"

access_token = refresh_token()

# ヘッダー (curlコマンドのヘッダーから)
headers = {
    "Access-Token": access_token
    # GETリクエストの場合、通常 Content-Type は不要ですが、
    # APIによっては要求される場合もあります。
    # "Content-Type": "application/json"
}

# クエリパラメータ (curlコマンドのURLの ? 以降から)
business_id = os.getenv("TIKTOK_BUSINESS_ID")
video_id = "7301242590496705810"
#fields_list = ["item_id","create_time","thumbnail_url","share_url","embed_url","caption","video_views","likes","comments","shares","reach","video_duration","full_video_watched_rate","total_time_watched","average_time_watched","impression_sources","audience_countries","new_followers","profile_views","website_clicks"]

#video_idは必須なのでどうやって直接入れるか考えなくては（そのたびに更新していくとか？）
params = {
    "business_id": business_id,
    "video_id": video_id,
    #"fields": json.dumps(fields_list), # リストをJSON文字列に変換

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

                # ここから追加: JSONをファイルとして出力する処理
        # 現在の日時を取得してファイル名に使用
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # 出力ディレクトリの設定（存在しない場合は作成）
        output_dir = "tiktok_data"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"ディレクトリ '{output_dir}' を作成しました。")
        
        # ファイル名の作成（タイムスタンプとvideo_idを含む）
        filename = f"{output_dir}/tiktok_comments_{video_id}_{timestamp}.json"
        
        # JSONデータをファイルに書き込み
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nデータが正常に保存されました: {filename}")

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