import datetime

def get_date_n_days_ago(n: int) -> datetime.date:
    """
    今日からn日前の日付オブジェクトを取得する関数 (システムのローカルタイムゾーン基準)

    Args:
        n: 何日前の日付を取得するか

    Returns:
        n日前の日付オブジェクト
    """
    today = datetime.date.today()
    return today - datetime.timedelta(days=n)

def format_date_yyyymmdd(date_obj: datetime.date) -> str:
    """
    日付オブジェクトを 'YYYY-MM-DD' 形式の文字列に変換する関数

    Args:
        date_obj: 変換したい日付オブジェクト

    Returns:
        'YYYY-MM-DD' 形式の日付文字列
    """
    return date_obj.strftime('%Y-%m-%d')

# --- データ更新遅延を考慮した期間取得関数 ---

def get_date_range(start_days_ago: int, end_days_ago: int) -> tuple[str, str]:
     """
     システムのローカルタイムゾーンの「今日」から見て、
     指定された日数前の範囲の開始日と終了日を 'YYYY-MM-DD' 文字列で取得する関数。

     Args:
         start_days_ago: 開始日が今日から何日前か (例: 3日前なら 3)
         end_days_ago: 終了日が今日から何日前か (例: 2日前なら 2)

     Returns:
         (開始日の文字列 ('YYYY-MM-DD'), 終了日の文字列 ('YYYY-MM-DD')) のタプル
     """
     # 開始日オブジェクトを取得 (今日から start_days_ago 日前)
     start_date_obj = get_date_n_days_ago(start_days_ago)

     # 終了日オブジェクトを取得 (今日から end_days_ago 日前)
     end_date_obj = get_date_n_days_ago(end_days_ago)

     start_date_str = format_date_yyyymmdd(start_date_obj)
     end_date_str = format_date_yyyymmdd(end_date_obj)

     # 開始日と終了日の順序を保証
     # 通常、start_days_ago > end_days_ago となるはず（例: 3日前〜2日前）
     # もし誤って start_days_ago < end_days_ago と指定された場合（例: 2日前〜3日前）でも、
     # 日付の順序を正しく入れ替える
     if start_date_obj > end_date_obj:
          start_date_str, end_date_str = end_date_str, start_date_str

     return (start_date_str, end_date_str)