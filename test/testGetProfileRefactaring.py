import os
import requests
import json
from getDateforProfile import get_dates_from_sheet
from refresh_token import refresh_token
import pandas as pd
from dotenv import load_dotenv
import traceback # エラー詳細表示用

load_dotenv()

# --- グローバルな定数 ---
# APIエンドポイントURL
BASE_URL = "https://business-api.tiktok.com/open_api/v1.3/business/get/"

# 環境変数からBusiness IDを取得
BUSINESS_ID = os.getenv('TIKTOK_BUSINESS_ID')
if not BUSINESS_ID:
    print("エラー: 環境変数 'TIKTOK_BUSINESS_ID' が設定されていません。スクリプトの主要処理をスキップします。")
    # exit() ではなく、後続の処理で BUSINESS_ID が None かチェックするようにすると、
    # エラーメッセージだけ出してスクリプト自体は最後まで実行できます。

# 取得したいフィールドのリスト
FIELDS_LIST = ["username", "display_name","followers_count","total_likes", "video_views","unique_video_views","profile_views", "shares", "comments","engaged_audience","bio_link_clicks"]

# aggregate_data で使用するカラムリストもここにまとめておくのが良い
AGGREGATE_SUM_COLUMNS = ["unique_video_views", "engaged_audience", "shares",
                         "video_views", "profile_views", "comments", "bio_link_clicks"]
AGGREGATE_INCREASE_COLUMNS = ["followers_count", "total_likes"]
AGGREGATE_INFO_COLUMNS = ["username", "display_name"]


# --- aggregate_data 関数 (修正版: 期間情報を引数で受け取る) ---
def aggregate_data(response_data, start_date_str, end_date_str):
    """
    APIレスポンスからデータを集計する関数。
    指定された期間 (start_date_str, end_date_str) を表示および増加分計算に使用する。

    Args:
        response_data (dict): APIからのレスポンスJSONデータ
        start_date_str (str): 集計対象期間の開始日 ('YYYY-MM-DD')
        end_date_str (str): 集計対象期間の終了日 ('YYYY-MM-DD')

    Returns:
        dict or None: 集計結果の辞書、またはエラー時にNone
    """
    print(f"\n--- データ集計開始 ({start_date_str} から {end_date_str}) ---") # 引数の期間を表示
    try:
        # --- データの検証と抽出 ---
        if "data" not in response_data or not isinstance(response_data["data"], dict):
            print("警告: レスポンスに 'data' キーがないか、辞書形式ではありません。")
            if "message" in response_data:
                print(f"APIメッセージ: {response_data['message']}")
            return {"message": "データ形式不正", "date_range": f"{start_date_str} から {end_date_str}"}

        data_dict = response_data["data"]

        # 日別データ (metrics リスト) を取得
        if "metrics" not in data_dict or not isinstance(data_dict["metrics"], list):
            print("警告: レスポンスの 'data' 内に 'metrics' キーがないか、リスト形式ではありません。")
            # metrics がなくてもアカウント情報だけは返せるかもしれないので、処理を続けるか検討
            # ここでは一旦、集計不可として返す
            return {"message": "日別データ(metrics)なし", "date_range": f"{start_date_str} から {end_date_str}"}

        daily_data_raw = data_dict["metrics"]

        # アカウント情報を取得 (存在しない場合も考慮)
        account_info = {
            "username": data_dict.get("username", "不明"),
            "display_name": data_dict.get("display_name", "不明"),
            "followers_count_total": pd.to_numeric(data_dict.get("followers_count"), errors='coerce'), # 期間終了時点の累計
            "total_likes_total": pd.to_numeric(data_dict.get("total_likes"), errors='coerce')        # 期間終了時点の累計
        }
        # '不明' ではなく None にしたい場合は .get(key) or None のようにする

        # --- DataFrame への変換 ---
        df = None
        if daily_data_raw: # metrics リストが空でない場合
            try:
                df = pd.DataFrame(daily_data_raw)
                # 'date' カラムの存在チェックと変換
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
                    df = df.dropna(subset=['date']).sort_values(by='date').reset_index(drop=True)
                    if df.empty:
                        print("警告: 日付が有効な日別データが見つかりません。")
                        # DataFrameが空でもアカウント情報は返せるので、処理を続ける
                    else:
                         print(f"日別データからDataFrame作成完了 (形状: {df.shape})。カラム: {df.columns.tolist()}")
                else:
                    print("警告: 日別データに 'date' カラムがありません。増加分計算はできません。")
                    df = None # date がないと集計・増加分計算ができないので df を None に戻す

            except Exception as df_err:
                 print(f"DataFrame変換中にエラーが発生しました: {df_err}")
                 traceback.print_exc()
                 df = None # エラー時は df を None に

        else:
            print("情報: 日別データ(metrics)が空です。")


        # --- データ型の整備 (数値計算のためにfloatに変換) ---
        if df is not None:
            for col in AGGREGATE_SUM_COLUMNS + AGGREGATE_INCREASE_COLUMNS: # 定数リストを使用
                if col in df.columns:
                    # errors='coerce' で数値に変換できないものは NaN になる
                    df[col] = pd.to_numeric(df[col], errors='coerce')


        # --- 集計結果の初期化 ---
        result = {}
        result["date_range"] = f"{start_date_str} から {end_date_str}"
        result.update(account_info) # アカウント情報をマージ (累計値もここに含まれる)

        # --- 数値データの合計 (期間内の合計) ---
        # 指定された集計期間 (start_date_str - end_date_str) 内の日別データで合計
        if df is not None and 'date' in df.columns:
            df_for_sum = df[(df['date'] >= start_date_str) & (df['date'] <= end_date_str)]
            if df_for_sum.empty:
                 print(f"情報: 指定期間 ({start_date_str} - {end_date_str}) 内に合計対象の日別データがありません。")
                 for col in AGGREGATE_SUM_COLUMNS: result[col] = 0 # 合計は0
            else:
                 for col in AGGREGATE_SUM_COLUMNS: # 定数リストを使用
                     if col in df_for_sum.columns:
                         # fillna(0) で NaN を 0 として合計
                         result[col] = df_for_sum[col].fillna(0).sum()
                     else:
                         result[col] = 0 # データがないカラムも0で初期化
                         # print(f"情報: 合計対象のカラム '{col}' が日別データに含まれていません。")
        else:
             print("情報: 日別データがないか 'date' カラムがないため、期間合計は計算できません。")
             for col in AGGREGATE_SUM_COLUMNS: result[col] = 0 # 合計は0


        # --- 増加分の計算 (followers_count, total_likes) ---
        # 日別データの指定期間内の最初と最後の値から計算
        if df is not None and 'date' in df.columns:
            # 指定期間内のデータを抽出
            df_for_increase = df[(df['date'] >= start_date_str) & (df['date'] <= end_date_str)].copy() # SettingWithCopyWarning 対策でコピー

            if not df_for_increase.empty:
                # 期間内の最初と最後の日付の行を取得 (日付でソート済みのはず)
                start_row = df_for_increase.iloc[0]
                end_row = df_for_increase.iloc[-1]

                # 最初と最後の日付が異なるか確認
                if start_row['date'] != end_row['date']:
                    print(f"増加分計算に使用する日別データの日付: 開始={start_row['date']}, 終了={end_row['date']}")
                    for col in AGGREGATE_INCREASE_COLUMNS: # followers_count, total_likes
                        if col in df_for_increase.columns:
                            start_val = start_row.get(col) # pd.to_numeric済なのでそのまま取得
                            end_val = end_row.get(col)

                            # 両方の値が有効な数値 (NaNでない) かチェック
                            if pd.notna(start_val) and pd.notna(end_val):
                                increase = end_val - start_val
                                result[f"{col}_increase"] = increase
                                # 累計値は account_info から取得したものを優先 (APIレスポンス直下の値)
                                # result[f"{col}_total"] は account_info.update で既に入っているはず
                                # print(f"  {col}: 開始({start_row['date']})={start_val}, 終了({end_row['date']})={end_val}, 増加={increase}")
                            else:
                                print(f"警告: {col} の期間内開始({start_row['date']})または終了({end_row['date']})の値が数値ではありません。増加分計算不可。")
                                result[f"{col}_increase"] = "計算不可"
                        else:
                             result[f"{col}_increase"] = "計算不可 (カラムなし)"
                             print(f"警告: 増加分計算対象のカラム '{col}' が日別データに含まれていません。")

                else: # 期間内のデータが1日分しかない場合
                    print(f"情報: 指定期間 ({start_date_str} - {end_date_str}) の日別データは {start_row['date']} の1日分です。増加分は0として扱います。")
                    for col in AGGREGATE_INCREASE_COLUMNS:
                        result[f"{col}_increase"] = 0 # 増加分は0
                        # 累計値は account_info から取得したものを優先

            else:
                print(f"警告: 指定期間 ({start_date_str} - {end_date_str}) 内に増加分計算対象の日別データが見つかりません。")
                for col in AGGREGATE_INCREASE_COLUMNS:
                    result[f"{col}_increase"] = "計算不可 (期間内データなし)"

        else:
             print("警告: 日別データがないか 'date' カラムがないため、増加分は計算できません。")
             for col in AGGREGATE_INCREASE_COLUMNS:
                  result[f"{col}_increase"] = "計算不可 (日別データ/dateカラムなし)"


        # --- 結果の表示 ---
        print("\n--- 集計結果 ---")
        print(f"期間: {result.get('date_range', '不明')}")
        print(f"ユーザー名: {result.get('username', '不明')}")
        print(f"表示名: {result.get('display_name', '不明')}")

        print("\n[合計値 (期間内)]")
        for col in AGGREGATE_SUM_COLUMNS: # 定数リストを使用
            # result にキーが存在するかチェックしてから表示
            print(f"  {col}: {result.get(col, 'データなし')}")

        print("\n[増加分・累計値]")
        for col in AGGREGATE_INCREASE_COLUMNS: # 定数リストを使用
            increase_key = f"{col}_increase"
            total_key = f"{col}_total" # account_info から取得した累計値のキー
            print(f"  {col}:")
            print(f"    増加分 (期間内): {result.get(increase_key, '計算不可')}")
            # 累計値は pd.to_numeric で NaN になっている可能性もあるのでチェック
            total_val = result.get(total_key)
            print(f"    累計 (期間終了時点): {total_val if pd.notna(total_val) else '不明'}")


        print("--- データ集計終了 ---")
        return result

    except Exception as e:
        print(f"データ集計中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()
        # エラー発生時も部分的な情報を返すか、Noneを返すか検討
        # ここでは None を返す
        return None


# --- getProfileAPI 関数 (修正版: 期間を引数で受け取る) ---
# この関数内で API リクエスト用の params を構築する
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
        return {"message": "日付無効", "date_range": f"{start_date} から {end_date}"} # エラー情報を返す
    if not business_id or not fields_list or not access_token:
         print("エラー: APIリクエストに必要なパラメータ(business_id, fields, token)が不足しています。")
         return {"message": "パラメータ不足", "date_range": f"{start_date} から {end_date}"} # エラー情報を返す

    # APIリクエスト用のパラメータを構築 (引数で受け取った期間を使用)
    # ★ ここで params 辞書を定義します ★
    params = {
        "business_id": business_id, # 引数の business_id を使用
        "fields": json.dumps(fields_list), # 引数の fields_list を使用
        "start_date": start_date,  # 引数の start_date を使用
        "end_date": end_date      # 引数の end_date を使用
    }

    headers = {
        "Access-Token": access_token
    }

    print(f"Requesting URL: {BASE_URL}") # グローバル定数を使用
    print(f"Params: {params}") # 表示

    aggregated_data = None # 初期化

    try:
        # GETリクエストを実行
        response = requests.get(BASE_URL, headers=headers, params=params)
        response.raise_for_status()  # ステータスコードが 2xx でない場合に例外を発生させる

        print("\nResponse Status Code:", response.status_code)
        try:
            response_data = response.json()
            print("--- Raw API Response Data ---") # デバッグ用にレスポンス全体を出力
            print(json.dumps(response_data, indent=4, ensure_ascii=False)) # デバッグ用にレスポンス全体を出力
            # print("Response JSON:")
            # print(json.dumps(response_data, indent=4, ensure_ascii=False)) # 元のコメントアウト

            # 取得したレスポンスデータを集計関数に渡す
            # 集計関数にも、表示用に期間文字列を渡す
            # ★ aggregate_data 呼び出し時に期間情報を渡す ★
            aggregated_data = aggregate_data(response_data, start_date, end_date)

        except json.JSONDecodeError:
            print("エラー: APIレスポンスがJSON形式ではありません:")
            print(response.text)
            aggregated_data = {"message": "APIレスポンスJSONエラー", "raw_response": response.text, "date_range": f"{start_date} から {end_date}"}


    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTPエラーが発生しました ({start_date} - {end_date}): {http_err}")
        if http_err.response is not None:
            print(f"Response status code: {http_err.response.status_code}")
            try:
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


# --- メイン処理 ---
if __name__ == '__main__':
    print("--- TikTokデータ取得スクリプト開始 ---")

    # BUSINESS_ID が読み込めているかここで最終チェック
    if not BUSINESS_ID:
        print("エラー: ビジネスIDが取得できていないため、処理を中止します。")
        exit()

    # --- アクセストークン取得 ---
    # refresh_token() 関数は、環境変数などから認証情報を読み込み、
    # TikTok APIを呼び出して新しいアクセストークンを返すことを想定
    access_token = refresh_token() # refresh_token モジュール内で load_dotenv() している場合はここでは不要
    if not access_token:
        print("エラー: アクセストークンの取得に失敗しました。処理を中断します。")
        exit() # トークンがないとAPI呼び出しができないので終了
    print("アクセストークン取得完了。")

    # --- スプレッドシートから日付情報を取得 ---
    # get_dates_from_sheet() 関数は A2, B2, C2, D2 の4つの日付を返すことを想定
    print("\n--- スプレッドシートから日付情報を取得中 ---")
    user_start_date, user_end_date, default_start_date, default_end_date = get_dates_from_sheet()

    # ここで取得した結果を保存するためのリストなどを用意しても良い
    # all_results = []

    # --- デフォルト期間のデータ取得 ---
    print("\n--- デフォルト期間のデータ取得処理 ---")
    if default_start_date and default_end_date:
        print(f"スプレッドシート(C2/D2)から取得したデフォルト期間: {default_start_date} - {default_end_date}")
        # getProfileAPI にデフォルト期間を渡して呼び出す
        default_period_results = getProfileAPI(
            default_start_date,
            default_end_date,
            BUSINESS_ID, # グローバル定数を使用
            FIELDS_LIST, # グローバル定数を使用
            access_token # 取得済みトークンを使用
        )
        if default_period_results:
            # getProfileAPI 関数内で結果表示するようにしているので、ここでは特別な表示はしない
            pass
        else:
            print(f"デフォルト期間 ({default_start_date} - {default_end_date}) のデータ取得または集計に失敗しました。")
            # エラーメッセージは getProfileAPI 関数内で出力されているはず

    else:
        print("スプレッドシート(C2/D2)からデフォルト期間の日付が取得できなかったか、不完全なためスキップします。")
        print(f"(取得値: start='{default_start_date}', end='{default_end_date}')")


    # --- ユーザー指定期間のデータ取得 ---
    print("\n--- ユーザー指定期間のデータ取得処理 ---")
    # ユーザー指定期間の日付 (A2/B2) が有効な場合のみ実行
    if user_start_date and user_end_date:
        print(f"スプレッドシート(A2/B2)から取得したユーザー指定期間: {user_start_date} - {user_end_date}")
        # getProfileAPI にユーザー指定期間を渡して呼び出す
        user_specified_results = getProfileAPI(
            user_start_date,
            user_end_date,
            BUSINESS_ID, # グローバル定数を使用
            FIELDS_LIST, # グローバル定数を使用
            access_token # 取得済みトークンを使用
        )
        if user_specified_results:
            # getProfileAPI 関数内で結果表示するようにしているので、ここでは特別な表示はしない
            pass
        else:
            print(f"ユーザー指定期間 ({user_start_date} - {user_end_date}) のデータ取得または集計に失敗しました。")
            # エラーメッセージは getProfileAPI 関数内で出力されているはず
    else:
        print("スプレッドシート(A2/B2)からユーザー指定期間の日付が取得できなかったか、不完全なためスキップします。")
        print(f"(取得値: start='{user_start_date}', end='{user_end_date}')")

    # ここで all_results リストなどを使って、取得したすべての結果を後続処理に渡したり、まとめて表示したりできる

    print("\n--- TikTokデータ取得スクリプト終了 ---")