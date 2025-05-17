import requests
import json
#成功しました（4月17日）うまくいかなかった原因はMyAppのところで使うURLとスコープを間違えていたからだと思う。

# 4月20日追記：デフォルトでは、TikTokアカウントユーザーが以前に同じ権限で開発者アプリを承認している場合、ステップ2の「権限スコープの確認および承認ページ」はスキップされます。代わりに、TikTokアカウントユーザーは直接リダイレクトURLにリダイレクトされます。
# この自動リダイレクトの仕組みを無効にするには、TikTokアカウントユーザーに共有する認可URLの末尾に &disable_auto_auth=1 を手動で追加する必要があります。
# たとえば、元の認可URLが
# https://www.tiktok.com/v2/auth/authorize?{parameters}
# である場合、開発者は以下のURLを共有する必要があります：
# https://www.tiktok.com/v2/auth/authorize?{parameters}&disable_auto_auth=1
# ----- 設定値 -----
# 実際の値に置き換えてください
client_id = "7493061298511413249"
client_secret = "6eda48ddfdda858b36d9d2aa372d935e3bc00510"
auth_code = "L-yfrqq004rVilK-sfTymSAh1iROwrtU4mfz9S8a_IRExGdh3rriVutkI6q7VJLQA_UHMMK145PBDj3tdzoTW9VU5rp_u5f8XQpkl1QOD2fRVoeXgDlQ25F-X98wIEAVfxT9Ps83IeM93wOlrcEvXcnb8wOMqxXx4kkiAUP4hCGjNcByz3w1eTWfrFVGr-Nu5yphUncmSX_NpvBI5mtxsHBg6s5Plz8eIg2qWwJZr8ZfCNcEUvqJrPf54zU-0VvM%2A2%215262.va"
redirect_uri = "https://mates-promo.com/"
# ------------------

# APIエンドポイントURL
url = "https://business-api.tiktok.com/open_api/v1.3/tt_user/oauth2/token/"

# リクエストヘッダー
headers = {
    'Content-Type': 'application/json'
}

# リクエストボディ (ペイロード)
payload = {
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type": "authorization_code",
    "auth_code": auth_code,
    "redirect_uri": redirect_uri
}

try:
    # POSTリクエストを送信
    # requestsライブラリは自動的にリダイレクトに従います (`--location`相当)
    # jsonパラメータに辞書を渡すと、自動的にJSON文字列に変換し、
    # Content-Typeヘッダーを 'application/json' に設定します。
    # ここでは明示的にヘッダーも指定していますが、jsonパラメータだけでも十分な場合が多いです。
    response = requests.post(url, headers=headers, json=payload)

    # レスポンスステータスコードを確認 (エラーがあれば例外を発生させる)
    response.raise_for_status()

    # レスポンス内容をJSONとして取得
    response_data = response.json()

    # 結果を出力
    print("リクエスト成功")
    print("ステータスコード:", response.status_code)
    print("レスポンスボディ:")
    print(json.dumps(response_data, indent=4, ensure_ascii=False)) # きれいに整形して出力

except requests.exceptions.RequestException as e:
    # ネットワークエラーやHTTPエラーが発生した場合
    print(f"リクエストエラー: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print("ステータスコード:", e.response.status_code)
        try:
            # エラーレスポンスの内容も表示試行
            print("エラーレスポンスボディ:", e.response.text)
        except Exception:
            print("エラーレスポンスボディの読み取りに失敗しました。")

except json.JSONDecodeError:
    # レスポンスがJSON形式でなかった場合
    print("レスポンスのJSONデコードに失敗しました。")
    print("ステータスコード:", response.status_code)
    print("レスポンスボディ (生):", response.text)


