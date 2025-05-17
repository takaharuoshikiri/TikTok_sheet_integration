import datetime
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
#A2とB2のデータを読み取る
RANGE_NAME = 'getDate!A4:E4'

# --- 設定ここまで ---

def get_dates_from_sheet():
    """
    Google スプレッドシートから開始日と終了日を取得し、
    'YYYY-MM-DD' 形式の文字列のタプルとして返す。

    Returns:
        tuple: (start_date_str, end_date_str) のタプル。
               取得または変換に失敗した場合は (None, None) を返す。
    """
    creds = None
    video_day1 = None#いったん変数は初期化しておこう
    video_day2 = None
    video_day3 = None
    video_week1 = None
    video_week2 = None
    service = None

    try:
        # --- 認証 ---
        try:
            creds = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        except FileNotFoundError:
            print(f"エラー: 認証情報ファイルが見つかりません: {SERVICE_ACCOUNT_FILE}")
            return None, None # エラー時は None を返す
        except Exception as e:
            print(f"エラー: 認証情報の読み込み中にエラーが発生しました: {e}")
            return None, None

        # --- APIサービス構築 ---
        try:
            service = build('sheets', 'v4', credentials=creds)
        except Exception as e:
            print(f"エラー: Google Sheets API サービスの構築中にエラーが発生しました: {e}")
            return None, None

        # --- スプレッドシートからのデータ読み込み ---
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print(f"情報: 指定範囲 '{RANGE_NAME}' にデータが見つかりませんでした。")
            # データがない場合も None, None を返す
            return None, None
        else:
            row_data = values[0]
            value_a2 = row_data[0] if len(row_data) > 0 else None
            value_b2 = row_data[1] if len(row_data) > 1 else None
            value_c2 = row_data[2] if len(row_data) > 2 else None
            value_d2 = row_data[3] if len(row_data) > 3 else None

            print(f"'{RANGE_NAME}' から読み取った値: A2='{value_a2}', B2='{value_b2}'") # デバッグ用

            # --- A2 の値を start_date_def に変換 ---
            if value_a2:
                try:
                    dt_obj_a2 = None
                    # 様々な形式を試す (必要に応じて追加/削除)
                    possible_formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']
                    for fmt in possible_formats:
                        try:
                            dt_obj_a2 = datetime.datetime.strptime(str(value_a2), fmt)
                            break
                        except ValueError:
                            continue
                    # 数値シリアル値の試行
                    if dt_obj_a2 is None and isinstance(value_a2, (int, float)):
                        from datetime import timedelta, date
                        excel_epoch = datetime.date(1899, 12, 30) # Excel/Sheetsの基準日(要確認)
                        dt_obj_a2 = excel_epoch + timedelta(days=float(value_a2))

                    if dt_obj_a2:
                        start_date_def = dt_obj_a2.strftime('%Y-%m-%d')
                    else:
                        # どの形式にもマッチしなかった場合
                        print(f"警告: A2の値 '{value_a2}' を既知の日付形式に変換できませんでした。")

                except (ValueError, TypeError, AttributeError) as e:
                    print(f"警告: A2の値 '{value_a2}' の日付変換中にエラーが発生しました: {e}")
                except Exception as e:
                    print(f"警告: A2の値の処理中に予期せぬエラーが発生しました: {e}")

            # --- B2 の値を end_date_def に変換 (A2と同様) ---
            if value_b2:
                try:
                    dt_obj_b2 = None
                    possible_formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']
                    for fmt in possible_formats:
                         try:
                             dt_obj_b2 = datetime.datetime.strptime(str(value_b2), fmt)
                             break
                         except ValueError:
                             continue
                    if dt_obj_b2 is None and isinstance(value_b2, (int, float)):
                         from datetime import timedelta, date
                         excel_epoch = datetime.date(1899, 12, 30)
                         dt_obj_b2 = excel_epoch + timedelta(days=float(value_b2))

                    if dt_obj_b2:
                         end_date_def = dt_obj_b2.strftime('%Y-%m-%d')
                    else:
                         print(f"警告: B2の値 '{value_b2}' を既知の日付形式に変換できませんでした。")

                except (ValueError, TypeError, AttributeError) as e:
                    print(f"警告: B2の値 '{value_b2}' の日付変換中にエラーが発生しました: {e}")
                except Exception as e:
                    print(f"警告: B2の値の処理中に予期せぬエラーが発生しました: {e}")

                        # --- C2 の値を start_date に変換 ---
            if value_c2:
                try:
                    dt_obj_c2 = None
                    # 様々な形式を試す (必要に応じて追加/削除)
                    possible_formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']
                    for fmt in possible_formats:
                        try:
                            dt_obj_c2 = datetime.datetime.strptime(str(value_c2), fmt)
                            break
                        except ValueError:
                            continue
                    # 数値シリアル値の試行
                    if dt_obj_c2 is None and isinstance(value_a2, (int, float)):
                        from datetime import timedelta, date
                        excel_epoch = datetime.date(1899, 12, 30) # Excel/Sheetsの基準日(要確認)
                        dt_obj_c2 = excel_epoch + timedelta(days=float(value_c2))

                    if dt_obj_c2:
                        start_date = dt_obj_c2.strftime('%Y-%m-%d')
                    else:
                        # どの形式にもマッチしなかった場合
                        print(f"警告: A2の値 '{value_c2}' を既知の日付形式に変換できませんでした。")

                except (ValueError, TypeError, AttributeError) as e:
                    print(f"警告: A2の値 '{value_c2}' の日付変換中にエラーが発生しました: {e}")
                except Exception as e:
                    print(f"警告: A2の値の処理中に予期せぬエラーが発生しました: {e}")
                                # --- D2 の値を end_date に変換 ---
            if value_d2:
                try:
                    dt_obj_d2 = None
                    # 様々な形式を試す (必要に応じて追加/削除)
                    possible_formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']
                    for fmt in possible_formats:
                        try:
                            dt_obj_d2 = datetime.datetime.strptime(str(value_d2), fmt)
                            break
                        except ValueError:
                            continue
                    # 数値シリアル値の試行
                    if dt_obj_d2 is None and isinstance(value_d2, (int, float)):
                        from datetime import timedelta, date
                        excel_epoch = datetime.date(1899, 12, 30) # Excel/Sheetsの基準日(要確認)
                        dt_obj_d2 = excel_epoch + timedelta(days=float(value_d2))

                    if dt_obj_d2:
                        end_date = dt_obj_d2.strftime('%Y-%m-%d')
                    else:
                        # どの形式にもマッチしなかった場合
                        print(f"警告: A2の値 '{value_d2}' を既知の日付形式に変換できませんでした。")

                except (ValueError, TypeError, AttributeError) as e:
                    print(f"警告: A2の値 '{value_d2}' の日付変換中にエラーが発生しました: {e}")
                except Exception as e:
                    print(f"警告: A2の値の処理中に予期せぬエラーが発生しました: {e}")

            # --- ★★★取得した日付文字列をタプルで返す★★★ ---
            print(f"変換結果: start_date_def='{start_date_def}', end_date_def='{end_date_def}',start_date='{start_date}', end_date='{end_date}'") # デバッグ用
            return start_date_def, end_date_def, start_date, end_date

    except HttpError as err:
        print(f"APIエラー: {err}")
        return None, None # APIエラー時も None を返す
    except Exception as e:
        print(f"日付取得処理中に予期せぬエラー: {e}")
        return None, None # その他のエラー時も None を返す

# --- このファイル単体で実行した場合のテスト用 ---
if __name__ == "__main__":
    print("--- get_sheet_dates.py を直接実行 ---")
    s_date, e_date,s_date_def, e_date_def = get_dates_from_sheet()
    if s_date and e_date:
        print(f"テスト取得成功: 開始日={s_date_def}, 終了日={e_date_def} デフォルト：開始日={s_date}, 終了日={e_date}")
    else:
        print("テスト取得失敗。")
    print("--- 直接実行終了 ---")