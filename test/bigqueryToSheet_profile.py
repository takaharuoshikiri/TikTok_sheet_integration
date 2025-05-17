import pandas as pd
import os
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

# 設定パラメータ
PROJECT_ID =  os.getenv("PROJECT_ID") # Google Cloud プロジェクトID
DATASET_NAME =  os.getenv("DATASET_ID") # BigQueryデータセット名
TABLE_NAME = 'ProfileDataNo1'   # BigQueryテーブル名.envに書くべきだがいっぱいテーブルあるのでいいったんゴミハードコーディング
SPREADSHEET_ID = os.getenv("PROFILE_SHEET")  # Google SpreadsheetのID
WORKSHEET_NAME = 'profile'  # ワークシート名
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")  # サービスアカウントのJSONファイル

# 英語から日本語へのフィールド名マッピング
FIELD_MAPPING = {
    'username': 'ユーザー名',
    'metrics_date': '日付',
    'metrics_unique_video_views': 'ユニーク視聴回数',
    'metrics_profile_views': 'プロフィール閲覧数',
    'metrics_shares': 'シェア数',
    'metrics_comments': 'コメント数',
    'metrics_engaged_audience': 'エンゲージメント数',
    'metrics_bio_link_clicks': 'リンククリック数',
    'metrics_video_views': '動画視聴回数',
    'total_likes': 'いいね数',
    'processed_at': '処理日時'
}

def get_bigquery_data():
    """BigQueryからデータを取得する"""
    # BigQuery クライアントの初期化
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    client = bigquery.Client(credentials=creds, project=PROJECT_ID)
    
    # 7日前からのデータを取得するクエリ
    query = f"""
    SELECT
      username,               
      metrics_date,               
      metrics_unique_video_views, 
      metrics_profile_views,
      metrics_shares,              
      metrics_comments,            
      metrics_engaged_audience,  
      metrics_bio_link_clicks,     
      metrics_video_views,         
      total_likes,              
      processed_at              
    FROM
      `{PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}`
    WHERE
      metrics_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    ORDER BY
      username, metrics_date ASC
    """
    
    # クエリ実行
    query_job = client.query(query)
    results = query_job.result()
    
    # pandasデータフレームに変換
    df = results.to_dataframe()
    
    # 列名を日本語に変更
    df.rename(columns=FIELD_MAPPING, inplace=True)
    
    print(f"BigQueryから{len(df)}行のデータを取得しました")
    return df

def update_spreadsheet(df):
    """スプレッドシートにデータを更新する"""
    # Google Sheetsへのアクセス設定
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file' # スプレッドシートのメタデータアクセスに必要
    ]
    
    credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(credentials)
    
    # スプレッドシートを開く
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    
    # 現在のシートの内容を取得
    existing_data = sheet.get_all_values()
    
    # ヘッダー行を常に設定する（毎回更新）
    headers = list(FIELD_MAPPING.values())
    sheet.update('A1', [headers])
    start_row = 2  # データの書き込み開始行
    
    # 日付/日時型カラムを特定し、文字列に変換
    # BigQueryのDATE, DATETIME, TIMESTAMP は pandas ではそれぞれ dbdate, datetime64[ns] になることが多い
    for col in df.columns:
        # dtype を確認して日付/時刻関連のカラムを処理
        if pd.api.types.is_datetime64_any_dtype(df[col]) or 'dbdate' in str(df[col].dtype):
            # NaT (Not a Time) を空文字などに変換したい場合は .fillna('') を追加することも可能
            # df[col] = df[col].astype(str).replace('NaT', '')
            df[col] = df[col].astype(str) # ISO 8601形式の文字列 ('YYYY-MM-DD' や 'YYYY-MM-DD HH:MM:SS.ffffff') に変換
        # Pythonネイティブの date オブジェクトが object 型として含まれる場合も考慮 (稀なケース)
        elif df[col].dtype == 'object':
            # 特定のカラム名で判断するか、より厳密な型チェックを行う
            if col in ['日付', '処理日時']: # BigQueryクエリのエイリアス名で指定
                # apply を使って各要素を安全に文字列変換 (None や NaT を考慮)
                df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) and hasattr(x, 'isoformat') else str(x) if pd.notnull(x) else None)
    
    # データをリストに変換
    data_values = df.values.tolist()
    
    # スプレッドシートに書き込み
    if data_values:
        try:
            # キーワード引数を使用し、value_input_option を指定
            sheet.update(range_name=f'A{start_row}',
                        values=data_values,
                        value_input_option='USER_ENTERED') # または 'RAW'
            print(f"スプレッドシートに{len(data_values)}行のデータを更新しました") # 成功時にメッセージ表示

        # --- ここから追加 ---
        except gspread.exceptions.APIError as e:
            print(f"Google Sheets APIエラーが発生しました: {e}")
            # エラーの詳細を知りたい場合、レスポンス内容を出力
            # import json
            # print(f"APIエラー詳細: {json.dumps(e.response.json(), indent=2)}")
            return False # エラーが発生したことを示す
        except Exception as e:
            print(f"スプレッドシート更新中に予期せぬエラーが発生しました: {e}")
            return False # エラーが発生したことを示す
            # --- ここまで追加 ---
    else:
        print("書き込むデータがありません。")

        return True # 正常に処理が完了した場合 (書き込むデータがない場合も含む)

def main():
    """メイン処理"""
    print("TikTokデータ連携処理を開始します")
    
    # BigQueryからデータを取得
    df = get_bigquery_data()
    
    # データが空でないか確認
    if df.empty:
        print("取得したデータが空です")
        return
        
    # スプレッドシートを更新
    update_spreadsheet(df)
    
    print("TikTokデータ連携処理が正常に完了しました")
    
if __name__ == "__main__":
    main()