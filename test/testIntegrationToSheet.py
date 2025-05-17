import gspread
from google.oauth2.service_account import Credentials
import datetime

# 4月20日venvの仮想環境を用いて、gspreadは仮想環境にのみpip　installしているダミーデータを入力することに成功
# 1から4の設定をちゃんと入力すれば動く

# --- 設定 (### 要変更 ###) ---
# 1. Google Sheets APIのスコープ (通常はこのままでOK)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file' # スプレッドシートのメタデータアクセスに必要
]

# 2. ダウンロードしたサービスアカウントキー(JSON)ファイルのパス
#    Windowsの例: 'C:/Users/YourUser/Documents/.secrets/service_account_key.json'
#    macOS/Linuxの例: '/Users/youruser/projects/.secrets/service_account_key.json'
SERVICE_ACCOUNT_FILE = '../.seacrets/isentropic-now-457219-t2-ffcae5667fbe.json'

# 3. 書き込みたいスプレッドシートのID
#    スプレッドシートのURLの /d/ と /edit の間にある長い文字列です
#    例: https://docs.google.com/spreadsheets/d/【ここに表示されているのがID】/edit#gid=0
SPREADSHEET_ID = '1IA4LaHgI_BZZMpvtBxTbHqpMwTuKxzId_QWzGD_PpYE'

# 4. 書き込みたいシートの名前
#    例: 'シート1', 'TikTokデータ' など
SHEET_NAME = 'シート1'
# --- 設定ここまで ---

def write_dummy_data_to_sheet():
    """
    サービスアカウントを使って認証し、ダミーデータをスプレッドシートに追記する関数
    """
    try:
        # サービスアカウントキーを使って認証情報を生成
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        # gspreadクライアントを認証情報で初期化
        client = gspread.authorize(creds)

        # スプレッドシートIDでシートを開く
        spreadsheet = client.open_by_key(SPREADSHEET_ID)

        # シート名でワークシートを選択
        worksheet = spreadsheet.worksheet(SHEET_NAME)

        # --- 書き込むダミーデータの作成 ---
        # 現在の日時を取得
        now = datetime.datetime.now()
        current_date = now.strftime("%Y-%m-%d") # YYYY-MM-DD形式
        current_time = now.strftime("%H:%M:%S") # HH:MM:SS形式

        # 例: [取得日, 動画ID, いいね数, コメント数] のようなデータ
        dummy_data = [
            [current_date, f"dummy_video_{current_time}_A", 123, 45],
            [current_date, f"dummy_video_{current_time}_B", 678, 90],
        ]

        print(f"以下のデータをシート '{SHEET_NAME}' に追記します:")
        for row in dummy_data:
            print(row)

        # --- シートへのデータ追記 ---
        # append_rowsはリストのリストを受け取り、シートの最後の空行から追記する
        worksheet.append_rows(dummy_data)

        print("\nデータの追記が成功しました！")

    except FileNotFoundError:
        print(f"エラー: サービスアカウントキーファイルが見つかりません。パスを確認してください: {SERVICE_ACCOUNT_FILE}")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"エラー: スプレッドシートが見つかりません。IDを確認してください: {SPREADSHEET_ID}")
    except gspread.exceptions.WorksheetNotFound:
        print(f"エラー: シートが見つかりません。シート名を確認してください: {SHEET_NAME}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

# スクリプトが直接実行された場合にのみ関数を呼び出す
if __name__ == '__main__':
    write_dummy_data_to_sheet()