from flask import Flask, redirect, request, session, url_for
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # CSRF防止に使う

# TikTokアプリの情報
CLIENT_KEY = 'あなたのクライアントキー'
CLIENT_SECRET = 'あなたのクライアントシークレット'
REDIRECT_URI = 'http://localhost:5000/callback'

# 認証のスコープ
SCOPE = 'user.info.basic,video.list'

@app.route('/')
def index():
    # TikTokの認証URLへリダイレクト
    tiktok_auth_url = (
        'https://www.tiktok.com/v2/auth/authorize/?'
        f'client_key={CLIENT_KEY}'
        f'&scope={SCOPE}'
        '&response_type=code'
        f'&redirect_uri={REDIRECT_URI}'
        '&state=xyz123'
    )
    return redirect(tiktok_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return 'Error: Authorization code not found.'

    # アクセストークンの取得
    url = 'https://open-api.tiktok.com/oauth/access_token/'
    payload = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }

    res = requests.post(url, json=payload)
    data = res.json()

    if 'data' in data:
        access_token = data['data']['access_token']
        refresh_token = data['data']['refresh_token']
        open_id = data['data']['open_id']
        scope = data['data']['scope']

        return f"""
        <h2>認証成功</h2>
        <p>Open ID: {open_id}</p>
        <p>Access Token: {access_token}</p>
        <p>Refresh Token: {refresh_token}</p>
        <p>Scope: {scope}</p>
        """
    else:
        return f"エラー発生: {data}"

if __name__ == '__main__':
    app.run(debug=True)
