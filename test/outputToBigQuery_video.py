import json
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
import datetime
import logging

    # --- 設定 ---
# !! WARNING: セキュリティのため、コードに直接書き込まず、環境変数などから取得することを強く推奨します !!
SERVICE_ACCOUNT_FILE = '../.seacrets/isentropic-now-457219-t2-ffcae5667fbe.json' # <--- あなたのファイルパスに修正

PROJECT_ID = 'isentropic-now-457219-t2' # <--- あなたのGCPプロジェクトIDに修正
DATASET_ID = 'TikTok_insight_tool'     # <--- あなたのデータセットIDに修正
TABLE_NAME = 'ProfileDataNo1'         # <--- あなたのテーブル名に修正


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

def upload_tiktok_data_to_bigquery(json_data, project_id, dataset_id, table_id, service_account_file):
    """
    TikTokのAPIデータをBigQueryにアップロードする関数
    
    Args:
        json_data (str or dict): JSONデータ（文字列またはdict形式）
        project_id (str): Google Cloudプロジェクトのプロジェクトファイル
        dataset_id (str): BigQueryデータセットのID
        table_id (str): BigQueryテーブルのID
        service_account_file (str): SERVICE_ACCOUNT_FILEのパス
        
    Returns:
        bool: 処理が成功した場合はTrue、失敗した場合はFalse
    """

    try:
        # JSONデータをパース（文字列の場合）
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        # BigQueryクライアントの初期化
        client = build_bigquery_client(service_account_file, project_id)
        
        # クライアントが正常に構築されなかった場合はエラー
        if client is None:
            return False
        
        # アカウント情報とメトリクス情報をフラット化
        flattened_data = []
        
        # アカウント基本情報を抽出
        account_info = {
            'request_id': data.get('request_id', ''),
            'username': data.get('data', {}).get('username', ''),
            'display_name': data.get('data', {}).get('display_name', ''),
            'total_likes': data.get('data', {}).get('total_likes', 0),
            'followers_count': data.get('data', {}).get('followers_count', 0),
            'processed_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # メトリクス配列をフラット化して各日付のデータを処理
        for metric in data.get('data', {}).get('metrics', []):
            row = account_info.copy()  # アカウント基本情報をコピー
            
            # メトリクス情報を追加
            row.update({
                'metrics_date': metric.get('date', ''),
                'metrics_video_views': metric.get('video_views', 0),
                'metrics_unique_video_views': metric.get('unique_video_views', 0),
                'metrics_profile_views': metric.get('profile_views', 0),
                'metrics_comments': metric.get('comments', 0),
                'metrics_shares': metric.get('shares', 0),
                'metrics_engaged_audience': metric.get('engaged_audience', 0),
                'metrics_bio_link_clicks': metric.get('bio_link_clicks', 0)
            })
            
            flattened_data.append(row)
        
        # データをBigQueryにアップロード
        if flattened_data:
            # 既存テーブルへのリファレンスを取得
            table_ref = f"{project_id}.{dataset_id}.{table_id}"
            
            # データのアップロード（スキーマ定義なし）
            job_config = bigquery.LoadJobConfig(
                # 既存のテーブルに追加
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                # 自動スキーマ検出
                autodetect=False
            )
            
            job = client.load_table_from_json(flattened_data, table_ref, job_config=job_config)
            job.result()  # アップロード完了を待機
            
            print(f"Successfully uploaded {len(flattened_data)} rows to {table_ref}")
            return True
            
    except Exception as e:
        print(f"Error uploading data to BigQuery: {str(e)}")
        logging.error(f"BigQuery upload error: {str(e)}")
        return False
# 使用例
if __name__ == "__main__":
    # テスト用の設定
    # --- 設定 ---
    # !! WARNING: セキュリティのため、コードに直接書き込まず、環境変数などから取得することを強く推奨します !!
    SERVICE_ACCOUNT_FILE = '../.seacrets/isentropic-now-457219-t2-ffcae5667fbe.json' # <--- あなたのファイルパスに修正

    PROJECT_ID = 'isentropic-now-457219-t2' # <--- あなたのGCPプロジェクトIDに修正
    DATASET_ID = 'TikTok_insight_tool'     # <--- あなたのデータセットIDに修正
    TABLE_NAME = 'ProfileDataNo1'         # <--- あなたのテーブル名に修正
 
    # JSONファイルからデータを読み込む例
    with open("tiktok_data/tiktok_profile_20250428_112906.json", "r", encoding="utf-8") as f:
        json_data = f.read()
    
    # BigQueryにアップロード
    upload_tiktok_data_to_bigquery(
        json_data=json_data,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_NAME,
        service_account_file=SERVICE_ACCOUNT_FILE
    )