import os
import gspread
import gspread_dataframe as gd
import pandas as pd
from google.oauth2.service_account import Credentials
import datetime
from testGetProfileData import getProfileAPI
from dotenv import load_dotenv

# 4月20日venvの仮想環境を用いて、gspreadは仮想環境にのみ"pip install gspreads"して、ダミーデータを入力することに成功
# 1から4の設定をちゃんと入力すれば動く、こいつはあくまでも書き込みをするための男

#4月21日日付指定して差分を取得できるようになったgetProfile.pyからデータを取得、加工して（dataflameの利用）によってシートに反映が可能になった（リストの順番がそのまま反映された）
#4月21日リフレッシュからAPIによるデータ取得、シートからのデータ取得、をして加工したデータをシートへ入力する処理が完了
load_dotenv()
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
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
# 4. 書き込みたいシートの名前
#    例: 'シート1', 'TikTokデータ' など
SHEET_NAME = 'testTikTok'
# --- 設定ここまで ---

#APIで取得したデータを持ってくる
#このprofileDataのリストの順番が、そのままスプレッドシートに書き込まれる列の順番になる。
profileData = getProfileAPI()
print(profileData)

keys = [
    'username', 'display_name', 'unique_video_views', 'engaged_audience',
    'shares', 'video_views', 'profile_views', 'comments',
    'followers_count_increase', 'followers_count_total',
    'total_likes_increase', 'total_likes_total',"bio_link_clicks",'date_range'
]

en_to_jp = {
    'username': 'ユーザー名',
    'display_name': '表示名',
    'unique_video_views': 'ユニーク動画再生数',
    'engaged_audience': 'エンゲージした視聴者',
    'shares': 'シェア数',
    'video_views': '動画再生数',
    'profile_views': 'プロフィール閲覧数',
    'comments': 'コメント数',
    'followers_count_increase': 'フォロワー増加数',
    'followers_count_total': 'フォロワー総数',
    'total_likes_increase': 'いいね増加数',
    'total_likes_total': 'いいね総数',
    'bio_link_clicks': 'リンククリック数',
    'date_range': '期間'
}

#いったん空のリストを作成
listData = []
#空のリストにvalueという変数に追加した各々の値をリストに追加
for key in keys:
    if key != 'date_range':
        value = profileData.get(key, "")
        jp_key = en_to_jp.get(key, key)
        listData.append(value) 
print(listData)


# print("前処理開始")
# exit()  # ここで強制終了
# print("この行は実行されません")

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

def write_profileData_to_sheet():
    """
    サービスアカウントを使って認証し、プロファイルデータをスプレッドシートに追記する関数
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

        print(f"以下のデータをシート '{SHEET_NAME}' に追記します:")
        print(listData)

        # リストをPandasのDataFrameに変換→gspread_dataflameを利用するにあたって必要（そもそもgspread_dataflameはpandasのdataflameを利用するためのもの）
        # 日本語の列名を取得（date_rangeを除く）
        jp_columns = [en_to_jp[k] for k in keys if k != 'date_range']

        # 日本語の列名でDataFrameを作成
        df = pd.DataFrame([listData], columns=jp_columns)

        output_columns = ['動画再生数', 'プロフィール閲覧数', 'フォロワー増加数', 'リンククリック数']
        output_df = df[output_columns]

        # 必要な列だけを含む新しいDataFrameを作成
        selected_data = []
        for col in output_columns:
            selected_data.append(df[col].values[0])  # 最初の行の値を取得

        # または列名と値のペアを1列ずつ出力
        pairs_df = pd.DataFrame({
            '項目': output_columns,
            '値': selected_data
        })
        # 横向きに出力するために転置
        transposed_df = pairs_df.transpose()

        #debug
        print("元のDataFrameの列名:", df.columns.tolist())
        print("出力用DataFrameの列名:", output_df.columns.tolist())
        print("出力用DataFrameの内容:")
        print(output_df)
        
        # DataFrameをシートに書き込み
        gd.set_with_dataframe(worksheet, transposed_df)

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
    write_profileData_to_sheet()
