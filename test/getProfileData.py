import os
import requests
import json
from getDateforProfile import get_dates_from_sheet
from refresh_token import refresh_token
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# --- グローバルな定数 (モジュールレベル定数) ---

# APIエンドポイントURL (基本的に変わらない)
BASE_URL = "https://business-api.tiktok.com/open_api/v1.3/business/get/"

# 環境変数からBusiness IDを取得 (スクリプト全体で使われる可能性が高い)
# load_dotenv() の後に配置すること
BUSINESS_ID = os.getenv('TIKTOK_BUSINESS_ID')

# 取得したいフィールドのリスト (通常固定)
FIELDS_LIST = ["username", "display_name", "followers_count", "total_likes",
               "video_views", "unique_video_views", "profile_views", "shares",
               "comments", "engaged_audience", "date_range" ,"bio_link_clicks"]

#aggregate_data内で使うリストもおいておいてよいかも

url = "https://business-api.tiktok.com/open_api/v1.3/business/get/"
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

def getProfileAPI(start_date, end_date, business_id, fields_list, access_token):

    """
    指定された期間のTikTokビジネスデータをAPIから取得し、集計・表示する関数。

    Args:
        start_date (str): 取得したい期間の開始日 ('YYYY-MM-DD')
        end_date (str): 取得したい期間の終了日 ('YYYY-MM-DD')
        business_id (str): TikTok Business ID
        fields_list (list): 取得したいフィールドのリスト
        access_token (str): 有効なアクセストークン

    Returns:
        dict or None: 集計結果の辞書、またはエラー時にNone
    """
    print(f"\n=== APIリクエスト開始 ({start_date} から {end_date}) ===")
    # 必須パラメータのチェック
    if not start_date or not end_date:
        print(f"エラー: 開始日 ({start_date}) または終了日 ({end_date}) が無効です。APIリクエストをスキップします。")
        return None
    if not business_id or not fields_list or not access_token:
         print("エラー: APIリクエストに必要なパラメータ(business_id, fields, token)が不足しています。")
         return None

    headers = {
        "Access-Token": access_token
    }

    print(f"Requesting URL: {BASE_URL}")
    print(f"Params: {params}") # 機密情報を含まないパラメータは表示してもOK

    aggregated_data = None # 初期化

    try:
        # GETリクエストを実行
        response = requests.get(BASE_URL, headers=headers, params=params)
        response.raise_for_status()  # ステータスコードが 2xx でない場合に例外を発生させる

        print("\nResponse Status Code:", response.status_code)
        try:
            response_data = response.json()
            # print("Response JSON:") # レスポンスJSON全体は大きい場合や機密を含む場合があるので、必要ならコメント解除
            # print(json.dumps(response_data, indent=4, ensure_ascii=False))

            # 取得したレスポンスデータを集計関数に渡す
            # 集計関数にも、表示用に期間文字列を渡す
            aggregated_data = aggregate_data(response_data)

        except json.JSONDecodeError:
            print("エラー: APIレスポンスがJSON形式ではありません:")
            print(response.text)
            aggregated_data = {"message": "APIレスポンスJSONエラー", "raw_response": response.text, "date_range": f"{start_date} から {end_date}"}


    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTPエラーが発生しました ({start_date} - {end_date}): {http_err}")
        if http_err.response is not None:
            print(f"Response status code: {http_err.response.status_code}")
            try:
                # エラーレスポンスの詳細を表示
                error_content = http_err.response.json()
                print(f"エラー内容 (JSON): {json.dumps(error_content, indent=2, ensure_ascii=False)}")
                aggregated_data = {"message": "API HTTPエラー", "status_code": http_err.response.status_code, "error_details": error_content, "date_range": f"{start_date} から {end_date}"}
            except json.JSONDecodeError:
                print(f"エラー内容 (Text): {http_err.response.text}")
                aggregated_data = {"message": "API HTTPエラー (JSON解析不可)", "status_code": http_err.response.status_code, "raw_response": http_err.response.text, "date_range": f"{start_date} から {end_date}"}
            except Exception as e:
                 print(f"エラーレスポンス処理中に別のエラー: {e}")
                 aggregated_data = {"message": "API HTTPエラー (詳細取得中エラー)", "status_code": http_err.response.status_code, "date_range": f"{start_date} から {end_date}"}

    except requests.exceptions.RequestException as req_err:
        print(f"\nリクエストエラーが発生しました ({start_date} - {end_date}): {req_err}")
        aggregated_data = {"message": "API リクエストエラー", "error_details": str(req_err), "date_range": f"{start_date} から {end_date}"}

    except Exception as e:
        import traceback
        print(f"\nAPIリクエストまたはデータ処理中に予期せぬエラーが発生しました ({start_date} - {end_date}): {e}")
        traceback.print_exc()
        aggregated_data = {"message": "予期せぬ処理エラー", "error_details": str(e), "date_range": f"{start_date} から {end_date}"}

    print(f"=== APIリクエスト終了 ({start_date} から {end_date}) ===")
    return aggregated_data # 集計結果またはエラー情報を返す

if __name__ == '__main__':
    print("--- TikTokデータ取得スクリプト開始 ---")

    # --- アクセストークン取得 ---
    # refresh_token() 関数は、環境変数などから認証情報を読み込み、
    # TikTok APIを呼び出して新しいアクセストークンを返すことを想定
    access_token = refresh_token()
    if not access_token:
        print("エラー: アクセストークンの取得に失敗しました。処理を中断します。")
        exit() # トークンがないとAPI呼び出しができないので終了
    print("アクセストークン取得完了。")

    # --- スプレッドシートから日付情報を取得 ---
    # get_dates_from_sheet() 関数は A2, B2, C2, D2 の4つの日付を返すことを想定
    print("\n--- スプレッドシートから日付情報を取得中 ---")
    user_start_date, user_end_date, default_start_date, default_end_date = get_dates_from_sheet()

    # ここで取得した結果を保存するためのリストなどを用意しても良い
    all_results = []

    # --- デフォルト期間のデータ取得 ---
    print("\n--- デフォルト期間のデータ取得処理 ---")
    if default_start_date and default_end_date:
        print(f"スプレッドシート(C2/D2)から取得したデフォルト期間: {default_start_date} - {default_end_date}")
        # getProfileAPI にデフォルト期間を渡して呼び出す
        default_period_results = getProfileAPI(default_start_date, default_end_date, BUSINESS_ID, FIELDS_LIST, access_token)
        if default_period_results:
            print("\n=== デフォルト期間 集計結果概要 ===")
            print(json.dumps(default_period_results, indent=2, ensure_ascii=False))
            # all_results.append({"period": "default", "data": default_period_results}) # 結果を保存する場合
        else:
            print(f"デフォルト期間 ({default_start_date} - {default_end_date}) のデータ取得または集計に失敗しました。")
    else:
        print("スプレッドシート(C2/D2)からデフォルト期間の日付が取得できなかったか、不完全なためスキップします。")
        print(f"(取得値: start='{default_start_date}', end='{default_end_date}')")


    # --- ユーザー指定期間のデータ取得 ---
    print("\n--- ユーザー指定期間のデータ取得処理 ---")
    # ユーザー指定期間の日付 (A2/B2) が有効な場合のみ実行
    if user_start_date and user_end_date:
        print(f"スプレッドシート(A2/B2)から取得したユーザー指定期間: {user_start_date} - {user_end_date}")
        # getProfileAPI にユーザー指定期間を渡して呼び出す
        user_specified_results = getProfileAPI(user_start_date, user_end_date, BUSINESS_ID, FIELDS_LIST, access_token)
        if user_specified_results:
            print("\n=== ユーザー指定期間 集計結果概要 ===")
            print(json.dumps(user_specified_results, indent=2, ensure_ascii=False))
            # all_results.append({"period": "user_specified", "data": user_specified_results}) # 結果を保存する場合
        else:
            print(f"ユーザー指定期間 ({user_start_date} - {user_end_date}) のデータ取得または集計に失敗しました。")
    else:
        print("スプレッドシート(A2/B2)からユーザー指定期間の日付が取得できなかったか、不完全なためスキップします。")
        print(f"(取得値: start='{user_start_date}', end='{user_end_date}')")

    # ここで all_results リストなどを使って、取得したすべての結果を後続処理に渡したり、まとめて表示したりできる

    print("\n--- TikTokデータ取得スクリプト終了 ---")