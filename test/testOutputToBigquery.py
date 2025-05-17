import os
import json
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

# Sheets API 関連は削除
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

# testGetVideoData.py から getVideoAPI 関数をインポート（要確認）
from testGetVideoData import getVideoAPI

# --- 設定 ---
# !! WARNING: セキュリティのため、コードに直接書き込まず、環境変数などから取得することを強く推奨します !!
SERVICE_ACCOUNT_FILE = '../.seacrets/isentropic-now-457219-t2-ffcae5667fbe.json' # <--- あなたのファイルパスに修正

PROJECT_ID = 'isentropic-now-457219-t2' # <--- あなたのGCPプロジェクトIDに修正
DATASET_ID = 'TikTok_insight_tool'     # <--- あなたのデータセットIDに修正
TABLE_NAME = 'videoDataNo1'         # <--- あなたのテーブル名に修正


def build_bigquery_client(key_file_path, project_id):
    if not os.path.exists(key_file_path):
        print(f"エラー: サービスアカウントキーファイルが見つかりません: {key_file_path}")
        return None
    try:
        creds = Credentials.from_service_account_file(key_file_path)
        client = bigquery.Client(credentials=creds, project=project_id)
        return client
    except Exception as e:
        print(f"エラー: BigQuery クライアントの構築中にエラーが発生しました: {e}")
        print(f"指定されたファイルパス: {key_file_path}")
        return None


def output():
    client = build_bigquery_client(SERVICE_ACCOUNT_FILE, PROJECT_ID)

    if client is None:
        print("BigQueryクライアントの構築に失敗したため、処理を中断します。")
        return

    response_dict = getVideoAPI()
    print(response_dict)
    print("実行したよね？？")

    if response_dict.get("code") != 0:
        print(f"APIからエラー応答が返されました: code={response_dict.get('code')}, message={response_dict.get('message')}")
        return

    # --- ここを修正 ---
    # APIレスポンス全体の辞書から "data" キーの値（ネストされた辞書）を取得
    api_data_payload = response_dict.get("data", {})

    # そのネストされた辞書から "videos" キーの値（動画データのリスト）を取得
    data_list = api_data_payload.get("videos", [])
    # --- 修正ここまで ---

    if not data_list:
        print("APIレスポンスに挿入対象のデータがありませんでした。")
        return

    try:
        df = pd.DataFrame(data_list)
    except Exception as e:
        print(f"APIレスポンスデータをDataFrameに変換中にエラーが発生しました: {e}")
        return

    if 'create_time' in df.columns:
        df['create_time'] = pd.to_datetime(df['create_time'], unit='s', errors='coerce')

    try:
        table_ref = client.dataset(DATASET_ID, project=PROJECT_ID).table(TABLE_NAME)
        # テーブルの存在確認は必須ではないので省略
        # table = client.get_table(table_ref)
    except Exception as e:
        print(f"エラー: BigQueryテーブル '{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}' の参照中にエラーが発生しました: {e}")
        return

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")

    try:
        job = client.load_table_from_dataframe(
            df, table_ref, job_config=job_config
        )

        # ジョブの完了を待機
        job.result()

        if job.state == 'DONE':
            if job.error_result:
                print("BigQueryロードジョブ中にエラーが発生しました:", job.error_result)
                for error in job.errors:
                    print(error)
            else:
                 # 成功時のメッセージは任意。最低限のエラー報告のみにするならこれも削除
                print(f"BigQueryテーブル '{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}' に {job.output_rows} 件のデータをロードしました。")
        else:
            print(f"BigQueryロードジョブは異常終了しました。状態: {job.state}")

    except Exception as e:
        print(f"BigQueryへのデータロード中に予期しないエラーが発生しました: {e}")


if __name__ == "__main__":
    output()