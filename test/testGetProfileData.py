import os
import requests
import json
import datetime
import pandas as pd
from dotenv import load_dotenv

from getDateforProfile import get_dates_from_sheet
from refresh_token import refresh_token
from outputToJson import outputToJson

"""
TikTok Business APIを使用してビジネスアカウント情報を取得する
API Doc: https://business-api.tiktok.com/portal/docs?id=1739940603393026 (推定されるドキュメント)
※注意: 上記ドキュメントURLは/business/get/に関する直接的なものではない可能性があります。
       正確なドキュメントはTikTok Business API Portalで確認してください。
"""
#4月21日testGetDatafromSheet.pyから日付のデータを獲得、指定した範囲でのデータの取得およびその開始日と終了日の差分を表示させることに成功。
load_dotenv()
# --- 設定 ---
# APIエンドポイント (curlコマンドのURLから)
# 注意: クエリパラメータは `params` 引数で渡すため、ベースURLのみを記述します
url = "https://business-api.tiktok.com/open_api/v1.3/business/get/"

# アクセストークン (curlコマンドのヘッダーから)
# 重要: このトークンはサンプルです。実際の有効なトークンに置き換えてください。
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
business_id = os.getenv('TIKTOK_BUSINESS_ID') # 実際のBusiness IDに置き換えてください
fields_list = ["username", "display_name","followers_count","total_likes", "video_views","unique_video_views","profile_views", "shares", "comments","engaged_audience","bio_link_clicks"]
start_date_def, end_date_def, start_date, end_date= get_dates_from_sheet() 


params = {
    "business_id": business_id,
    "fields": json.dumps(fields_list), # リストをJSON文字列に変換
    "start_date": start_date_def,
    "end_date": end_date_def
}
# print("実行してる？？")
def aggregate_data(response_data):
    """
    APIレスポンスからデータを集計する関数
    start_dateとend_dateの間の差分を計算
    """
    try:
        # データを取得
        if "data" in response_data:
            daily_data = response_data["data"]
        else:
            print("'data'キーが見つかりません。")
            return None
        
        # DataFrameに変換
        df = None
        if isinstance(daily_data, list):
            df = pd.DataFrame(daily_data)
        elif isinstance(daily_data, dict):
            if "videos" in daily_data:
                df = pd.DataFrame(daily_data["videos"])
            else:
                df = pd.DataFrame(daily_data)
            
            # メトリクスフィールドの平坦化
            if df is not None and not df.empty and 'metrics' in df.columns:
                # metricsフィールドの中から主要なフィールドを抽出
                metrics_fields = ['date', 'comments', 'profile_views', 'shares', 
                                'unique_video_views', 'engaged_audience', 
                                'followers_count', 'video_views',"bio_link_clicks"]
                for field in metrics_fields:
                    df[field] = df['metrics'].apply(lambda x: x.get(field, None) if isinstance(x, dict) else None)

        if df is None or df.empty:
            print("変換可能なデータが見つかりませんでした。")
            return None
        
        # 集計結果の辞書
        result = {}
        
        # 基本情報を取得
        if "username" in df.columns:
            result["username"] = df["username"].iloc[-1] if not df["username"].empty else "不明"
        
        if "display_name" in df.columns:
            result["display_name"] = df["display_name"].iloc[-1] if not df["display_name"].empty else "不明"
        
        # 数値データの合計
        numeric_columns = ["unique_video_views", "engaged_audience", "shares", 
                          "video_views", "profile_views", "comments","bio_link_clicks"]
        
        for col in numeric_columns:
            if col in df.columns:
                result[col] = df[col].astype(float).sum()
        
        # start_dateとend_dateに基づいて増加分を計算
        # APIから取得した開始日と終了日のデータを使用
        start_date = params["start_date"]  # APIリクエストで使用した開始日(デフォルト) 
        end_date = params["end_date"]      # APIリクエストで使用した終了日(デフォルト) 
        
        # 増加分を計算する対象
        increase_columns = ["followers_count", "total_likes"]
        
        for col in increase_columns:
            if col in df.columns:
                # 開始日のデータを取得
                start_data = df[df["date"] == start_date]
                # 終了日のデータを取得
                end_data = df[df["date"] == end_date]
                
                if not start_data.empty and not end_data.empty:
                    start_val = float(start_data[col].iloc[0])
                    end_val = float(end_data[col].iloc[0])
                    increase = end_val - start_val
                    
                    result[f"{col}_increase"] = increase
                    result[f"{col}_total"] = end_val
                else:
                    print(f"開始日または終了日のデータが見つかりません。日付の確認: {start_date}, {end_date}")
                    # 代替処理: 最初と最後のデータを使用
                    if len(df) >= 2:
                        start_val = float(df[col].iloc[0])
                        end_val = float(df[col].iloc[-1])
                        increase = end_val - start_val
                        
                        result[f"{col}_increase"] = increase
                        result[f"{col}_total"] = end_val
                        print(f"代替: 最初と最後のデータを使用して{col}の増加分を計算しました")
        
        # 日付範囲
        result["date_range"] = f"{start_date} から {end_date}"
        
        # 結果を表示
        print("\n=== 期間の集計結果 ===")
        
        # 合計値
        print("\n--- 合計値 ---")
        for col in numeric_columns:
            if col in result:
                print(f"{col}: {result[col]}")
        
        # 増加分
        print("\n--- 増加分 ---")
        for col in increase_columns:
            key = f"{col}_increase"
            if key in result:
                print(f"{key}: {result[key]}")
        
        # 累計値
        print("\n--- 累計値 ---")
        for col in increase_columns:
            key = f"{col}_total"
            if key in result:
                print(f"{key}: {result[key]}")
        
        # その他の情報
        print("\n--- その他の情報 ---")
        for key in ["username", "display_name", "date_range"]:
            if key in result:
                print(f"{key}: {result[key]}")
        
        return result
        
    except Exception as e:
        import traceback
        print(f"データ集計中にエラーが発生しました: {e}")
        traceback.print_exc()
        return None
    
# --- APIリクエストの実行,
def getProfileAPI():
    print(f"Requesting URL: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")

    try:
        # refresh_token()←いずれこの関数を用いて取得したトークンを代入する
        # print("refresh_complete")

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

            outputToJson(response_data)

            aggregated_data = aggregate_data(response_data)

            return aggregated_data

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


# --- メイン処理 ---
if __name__ == '__main__':
    
    getProfileAPI()
    